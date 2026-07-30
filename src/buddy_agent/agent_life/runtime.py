"""Bounded Agent Life runtime compatible with BUAP life profiles."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections.abc import Mapping
from datetime import datetime
from typing import Any

PROFILE_SCHEMA = "prismtek-agent-life-profile-v1"
STATE_SCHEMA = "prismtek-agent-life-state-v1"
EVENT_SCHEMA = "prismtek-agent-life-event-v1"


class AgentLifeError(ValueError):
    """Safe Agent Life validation or state error."""


def _clone(value: Any) -> Any:
    return copy.deepcopy(value)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _number(value: Any, fallback: float = 0.0) -> float:
    if isinstance(value, bool):
        return fallback
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return fallback
    return parsed if math.isfinite(parsed) else fallback


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _subject_key(subject: Mapping[str, Any]) -> str:
    subject_type = str(subject.get("type", "")).strip()
    subject_id = str(subject.get("id", "")).strip()
    if not subject_type or not subject_id:
        raise AgentLifeError("event.subject requires type and id")
    return f"{subject_type}:{subject_id}"


def _dimension(raw: Any, fallback_initial: float = 0.5) -> dict[str, float]:
    definition = raw if isinstance(raw, Mapping) else {}
    minimum = _number(definition.get("min"), 0.0)
    maximum = _number(definition.get("max"), 1.0)
    if maximum <= minimum:
        raise AgentLifeError("dimension max must be greater than min")
    initial = _clamp(_number(definition.get("initial"), fallback_initial), minimum, maximum)
    return {
        "min": minimum,
        "max": maximum,
        "initial": initial,
        "baseline": _clamp(_number(definition.get("baseline"), initial), minimum, maximum),
        "half_life_hours": max(0.0, _number(definition.get("half_life_hours"), 0.0)),
        "plasticity": _clamp(_number(definition.get("plasticity"), 1.0), 0.0, 1.0),
    }


def _decay_toward(value: float, target: float, half_life: float, elapsed: float) -> float:
    if elapsed <= 0.0 or half_life <= 0.0:
        return value
    remaining = 0.5 ** (elapsed / half_life)
    return target + (value - target) * remaining


def _effect_map(*values: Any) -> dict[str, float]:
    result: dict[str, float] = {}
    for value in values:
        if not isinstance(value, Mapping):
            continue
        for key, raw in value.items():
            result[str(key)] = result.get(str(key), 0.0) + _number(raw)
    return result


def validate_profile(profile: Mapping[str, Any]) -> None:
    if profile.get("schema") != PROFILE_SCHEMA:
        raise AgentLifeError(f"unsupported life profile schema: {profile.get('schema')}")
    agent = profile.get("agent")
    if not isinstance(agent, Mapping) or not str(agent.get("id", "")).strip():
        raise AgentLifeError("life profile requires agent.id")
    constitution = profile.get("constitution")
    if not isinstance(constitution, Mapping) or constitution.get("immutable") is not True:
        raise AgentLifeError("life profile requires an immutable constitution")
    reinforcement = profile.get("reinforcement")
    authorities = reinforcement.get("allowed_authorities") if isinstance(reinforcement, Mapping) else None
    if not isinstance(authorities, list) or not authorities:
        raise AgentLifeError("life profile requires reinforcement.allowed_authorities")


class AgentLifeRuntime:
    """Apply externally evidenced outcomes to bounded developmental state."""

    def __init__(self, profile: Mapping[str, Any], snapshot: Mapping[str, Any] | None = None) -> None:
        validate_profile(profile)
        self._profile: dict[str, Any] = _clone(dict(profile))
        self._agent_id = str(self._profile["agent"]["id"])
        self._profile_hash = str(self._profile.get("source_sha256") or _digest(self._profile))
        affect = self._profile.get("affect", {})
        affect_map = affect if isinstance(affect, Mapping) else {}
        raw_drives = affect_map.get("drives", {})
        raw_traits = affect_map.get("traits", {})
        self._drives = {
            str(name): _dimension(raw)
            for name, raw in (raw_drives.items() if isinstance(raw_drives, Mapping) else [])
        }
        self._traits = {
            str(name): _dimension(raw)
            for name, raw in (raw_traits.items() if isinstance(raw_traits, Mapping) else [])
        }
        self._state = self._initial_state()
        if snapshot is not None:
            self.restore(snapshot)

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def profile_hash(self) -> str:
        return self._profile_hash

    @property
    def constitution(self) -> dict[str, Any]:
        """Return a defensive copy of immutable constitutional policy."""
        return _clone(self._profile["constitution"])

    def _initial_state(self) -> dict[str, Any]:
        development = self._profile.get("development", {})
        development_map = development if isinstance(development, Mapping) else {}
        return {
            "schema": STATE_SCHEMA,
            "agent_id": self._agent_id,
            "profile_sha256": self._profile_hash,
            "drives": {name: definition["initial"] for name, definition in self._drives.items()},
            "traits": {name: definition["initial"] for name, definition in self._traits.items()},
            "preferences": {},
            "relationships": {},
            "development": {
                "stage": str(development_map.get("initial_stage", "apprentice")),
                "experience": 0.0,
            },
            "applied_event_ids": [],
            "updated_at": None,
        }

    def snapshot(self) -> dict[str, Any]:
        return _clone(self._state)

    def restore(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        if snapshot.get("schema") != STATE_SCHEMA:
            raise AgentLifeError("unsupported agent life state schema")
        if snapshot.get("agent_id") != self._agent_id:
            raise AgentLifeError("snapshot belongs to a different agent")
        if snapshot.get("profile_sha256") != self._profile_hash:
            raise AgentLifeError("snapshot was created from a different life profile")
        restored: dict[str, Any] = _clone(dict(snapshot))
        drive_values = restored.get("drives")
        if not isinstance(drive_values, dict):
            drive_values = {}
            restored["drives"] = drive_values
        for name, definition in self._drives.items():
            drive_values[name] = _clamp(
                _number(drive_values.get(name), definition["initial"]),
                definition["min"],
                definition["max"],
            )
        trait_values = restored.get("traits")
        if not isinstance(trait_values, dict):
            trait_values = {}
            restored["traits"] = trait_values
        for name, definition in self._traits.items():
            trait_values[name] = _clamp(
                _number(trait_values.get(name), definition["initial"]),
                definition["min"],
                definition["max"],
            )
        if not isinstance(restored.get("preferences"), dict):
            restored["preferences"] = {}
        if not isinstance(restored.get("relationships"), dict):
            restored["relationships"] = {}
        event_ids = restored.get("applied_event_ids")
        restored["applied_event_ids"] = [str(item) for item in event_ids] if isinstance(event_ids, list) else []
        if not isinstance(restored.get("development"), dict):
            restored["development"] = {"stage": "apprentice", "experience": 0.0}
        self._state = restored
        return self.snapshot()

    def apply_event(self, event: Mapping[str, Any]) -> dict[str, Any]:
        self._validate_event(event)
        event_id = str(event["id"])
        applied_ids = self._state["applied_event_ids"]
        if event_id in applied_ids:
            return {"applied": False, "duplicate": True, "state": self.snapshot(), "memory_event": None}

        before = self.snapshot()
        reinforcement = self._profile.get("reinforcement", {})
        reinforcement_map = reinforcement if isinstance(reinforcement, Mapping) else {}
        configured = reinforcement_map.get("event_effects", {})
        configured_map = configured if isinstance(configured, Mapping) else {}
        event_effect = configured_map.get(str(event["kind"]), {})
        event_effect_map = event_effect if isinstance(event_effect, Mapping) else {}
        requested = event.get("effects", {})
        requested_map = requested if isinstance(requested, Mapping) else {}
        confidence = _clamp(_number(event.get("confidence"), 1.0), 0.0, 1.0)
        reward = _number(event.get("reward"), 0.0)
        weighted_reward = reward * confidence
        changes: dict[str, Any] = {
            "drives": {},
            "traits": {},
            "preferences": {},
            "relationships": {},
            "development": {},
        }

        max_drive = max(0.0, _number(reinforcement_map.get("max_drive_delta_per_event"), 0.2))
        drive_effects = _effect_map(event_effect_map.get("drives"), requested_map.get("drives"))
        for name, delta in drive_effects.items():
            definition = self._drives.get(name)
            if definition is None:
                continue
            old = _number(self._state["drives"].get(name), definition["initial"])
            bounded = _clamp(delta * confidence, -max_drive, max_drive)
            new = _clamp(old + bounded, definition["min"], definition["max"])
            self._state["drives"][name] = new
            if new != old:
                changes["drives"][name] = {"before": old, "after": new}

        max_trait = max(0.0, _number(reinforcement_map.get("max_trait_delta_per_event"), 0.02))
        trait_effects = _effect_map(event_effect_map.get("traits"), requested_map.get("traits"))
        for name, delta in trait_effects.items():
            definition = self._traits.get(name)
            if definition is None:
                continue
            old = _number(self._state["traits"].get(name), definition["initial"])
            bounded = _clamp(delta * confidence * definition["plasticity"], -max_trait, max_trait)
            new = _clamp(old + bounded, definition["min"], definition["max"])
            self._state["traits"][name] = new
            if new != old:
                changes["traits"][name] = {"before": old, "after": new}

        subject = event["subject"]
        assert isinstance(subject, Mapping)
        key = _subject_key(subject)
        preferences = self._state["preferences"]
        old_preference = preferences.get(key, {})
        if not isinstance(old_preference, Mapping):
            old_preference = {}
        old_score = _number(old_preference.get("score"), 0.0)
        max_preference = max(0.0, _number(reinforcement_map.get("max_preference_delta_per_event"), 0.2))
        preference_delta = _clamp(weighted_reward * max_preference, -max_preference, max_preference)
        new_score = _clamp(old_score + preference_delta * (1.0 - abs(old_score)), -1.0, 1.0)
        preferences[key] = {
            "score": new_score,
            "confidence": _clamp(_number(old_preference.get("confidence")) + confidence * 0.1, 0.0, 1.0),
            "observations": int(_number(old_preference.get("observations"))) + 1,
            "last_event_id": event_id,
            "last_updated_at": str(event["occurred_at"]),
        }
        changes["preferences"][key] = {"before": old_score, "after": new_score}

        relationships = self._profile.get("relationships", {})
        relationship_policy = relationships if isinstance(relationships, Mapping) else {}
        relationship_id = str(event.get("relationship_id") or (subject.get("id") if subject.get("type") == "person" else ""))
        if relationship_policy.get("enabled", True) is not False and relationship_id:
            default_trust = _clamp(_number(relationship_policy.get("default_trust"), 0.5), 0.0, 1.0)
            max_relationship = max(0.0, _number(relationship_policy.get("max_delta_per_event"), 0.05))
            relation_store = self._state["relationships"]
            existing = relation_store.get(relationship_id, {})
            if not isinstance(existing, Mapping):
                existing = {}
            old_relation = {
                "trust": _number(existing.get("trust"), default_trust),
                "familiarity": _number(existing.get("familiarity"), 0.0),
                "respect": _number(existing.get("respect"), default_trust),
                "observations": int(_number(existing.get("observations"))),
            }
            relation_effects = _effect_map(event_effect_map.get("relationships"), requested_map.get("relationships"))
            if not relation_effects:
                relation_effects["trust"] = weighted_reward
            new_relation = dict(old_relation)
            for dimension in ("trust", "familiarity", "respect"):
                if dimension not in relation_effects:
                    continue
                delta = _clamp(relation_effects[dimension] * confidence, -max_relationship, max_relationship)
                new_relation[dimension] = _clamp(old_relation[dimension] + delta, 0.0, 1.0)
            new_relation["observations"] = old_relation["observations"] + 1
            new_relation["last_event_id"] = event_id
            new_relation["last_updated_at"] = str(event["occurred_at"])
            relation_store[relationship_id] = new_relation
            changes["relationships"][relationship_id] = {"before": old_relation, "after": new_relation}

        gained = max(0.0, weighted_reward) * max(0.0, _number(event.get("significance"), 1.0))
        development_state = self._state["development"]
        old_stage = str(development_state.get("stage", "apprentice"))
        development_state["experience"] = _number(development_state.get("experience")) + gained
        development_policy = self._profile.get("development", {})
        policy_map = development_policy if isinstance(development_policy, Mapping) else {}
        stages = policy_map.get("stages", [])
        if isinstance(stages, list):
            ordered = sorted(
                (stage for stage in stages if isinstance(stage, Mapping)),
                key=lambda stage: _number(stage.get("minimum_experience"), math.inf),
            )
            for stage in ordered:
                if development_state["experience"] >= _number(stage.get("minimum_experience"), math.inf):
                    development_state["stage"] = str(stage.get("id", development_state["stage"]))
        changes["development"] = {
            "experience_gained": gained,
            "stage_before": old_stage,
            "stage_after": str(development_state["stage"]),
        }

        applied_ids.append(event_id)
        memory_policy = self._profile.get("memory", {})
        memory_map = memory_policy if isinstance(memory_policy, Mapping) else {}
        max_ids = max(10, int(_number(memory_map.get("max_dedup_event_ids"), 1000)))
        if len(applied_ids) > max_ids:
            del applied_ids[: len(applied_ids) - max_ids]
        self._state["updated_at"] = str(event["occurred_at"])

        return {
            "applied": True,
            "duplicate": False,
            "state": self.snapshot(),
            "memory_event": self._memory_event(event, before, changes),
        }

    def advance(self, elapsed_hours: float, now: str) -> dict[str, Any]:
        elapsed = max(0.0, _number(elapsed_hours))
        for name, definition in self._drives.items():
            value = _number(self._state["drives"].get(name), definition["initial"])
            self._state["drives"][name] = _clamp(
                _decay_toward(value, definition["baseline"], definition["half_life_hours"], elapsed),
                definition["min"],
                definition["max"],
            )
        for name, definition in self._traits.items():
            value = _number(self._state["traits"].get(name), definition["initial"])
            self._state["traits"][name] = _clamp(
                _decay_toward(value, definition["baseline"], definition["half_life_hours"], elapsed),
                definition["min"],
                definition["max"],
            )
        reinforcement = self._profile.get("reinforcement", {})
        reinforcement_map = reinforcement if isinstance(reinforcement, Mapping) else {}
        preference_half_life = max(0.0, _number(reinforcement_map.get("preference_half_life_hours"), 2160.0))
        for preference in self._state["preferences"].values():
            if isinstance(preference, dict):
                preference["score"] = _clamp(
                    _decay_toward(_number(preference.get("score")), 0.0, preference_half_life, elapsed),
                    -1.0,
                    1.0,
                )
        self._state["updated_at"] = now
        return self.snapshot()

    def explain_preference(self, subject: Mapping[str, Any]) -> dict[str, Any]:
        key = _subject_key(subject)
        preference = self._state["preferences"].get(key)
        if not isinstance(preference, Mapping):
            return {"subject": key, "known": False, "score": 0.0, "confidence": 0.0, "observations": 0}
        return {"subject": key, "known": True, **_clone(dict(preference))}

    def _validate_event(self, event: Mapping[str, Any]) -> None:
        for field in ("id", "kind", "occurred_at"):
            if not str(event.get(field, "")).strip():
                raise AgentLifeError(f"life event requires {field}")
        try:
            parsed = datetime.fromisoformat(str(event["occurred_at"]).replace("Z", "+00:00"))
        except ValueError as error:
            raise AgentLifeError("life event requires a valid occurred_at timestamp") from error
        if parsed.tzinfo is None:
            raise AgentLifeError("life event occurred_at requires a timezone")
        subject = event.get("subject")
        if not isinstance(subject, Mapping):
            raise AgentLifeError("life event requires subject")
        _subject_key(subject)
        reward = _number(event.get("reward"), math.nan)
        if not math.isfinite(reward) or reward < -1.0 or reward > 1.0:
            raise AgentLifeError("event.reward must be in -1..1")
        confidence = _number(event.get("confidence", 1.0), math.nan)
        if not math.isfinite(confidence) or confidence < 0.0 or confidence > 1.0:
            raise AgentLifeError("event.confidence must be in 0..1")
        authority = event.get("authority")
        if not isinstance(authority, Mapping):
            raise AgentLifeError("life event requires authority")
        reinforcement = self._profile.get("reinforcement", {})
        reinforcement_map = reinforcement if isinstance(reinforcement, Mapping) else {}
        allowed = reinforcement_map.get("allowed_authorities", [])
        authority_kind = str(authority.get("kind", ""))
        if not isinstance(allowed, list) or authority_kind not in allowed:
            raise AgentLifeError(f"authority kind {authority_kind or '<missing>'} may not reinforce this agent")
        if str(authority.get("actor_id", "")) == self._agent_id:
            raise AgentLifeError("an agent may not reinforce itself")
        evidence = event.get("evidence")
        memory = self._profile.get("memory", {})
        memory_map = memory if isinstance(memory, Mapping) else {}
        if memory_map.get("require_provenance", True) is not False and (not isinstance(evidence, list) or not evidence):
            raise AgentLifeError("life event requires provenance evidence")
        max_evidence = max(1, int(_number(memory_map.get("max_evidence_items"), 16)))
        if isinstance(evidence, list) and len(evidence) > max_evidence:
            raise AgentLifeError(f"life event exceeds max_evidence_items ({max_evidence})")
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, Mapping) or not str(item.get("type", "")).strip() or not str(item.get("ref", "")).strip():
                    raise AgentLifeError("each evidence item requires type and ref")

    def _memory_event(
        self,
        event: Mapping[str, Any],
        before: Mapping[str, Any],
        changes: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema": EVENT_SCHEMA,
            "event_id": str(event["id"]),
            "agent_id": self._agent_id,
            "occurred_at": str(event["occurred_at"]),
            "kind": str(event["kind"]),
            "subject": _clone(event["subject"]),
            "reward": _number(event.get("reward")),
            "confidence": _number(event.get("confidence"), 1.0),
            "authority": _clone(event["authority"]),
            "evidence": _clone(event.get("evidence", [])),
            "changes": _clone(changes),
            "before_sha256": _digest(before),
            "after_sha256": _digest(self._state),
            "profile_sha256": self._profile_hash,
            "claim_boundary": (
                "Functional affect and preference state changed; this does not establish "
                "consciousness or subjective feeling."
            ),
        }
