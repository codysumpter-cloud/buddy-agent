from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prismtek_youtube_avatar_lipsync.py"


def load_module():
    spec = importlib.util.spec_from_file_location("buddy_lipsync", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_percentile_bounds() -> None:
    module = load_module()

    assert module.percentile([0.1, 0.2, 0.9], -1.0) == 0.1
    assert module.percentile([0.1, 0.2, 0.9], 2.0) == 0.9
    assert module.percentile([], 0.5) == 0.0


def test_mouth_states_handles_silence() -> None:
    module = load_module()

    states, stats = module.mouth_states([0.0, 0.0, 0.0], 1.0)

    assert states == [False, False, False]
    assert stats["open_ratio"] == 0.0


def test_mouth_states_opens_on_energy() -> None:
    module = load_module()

    states, stats = module.mouth_states([0.0, 0.02, 0.03, 0.0, 0.04], 1.0)

    assert any(states)
    assert 0.0 < stats["open_ratio"] <= 1.0


def test_audio_rms_rejects_invalid_fps() -> None:
    module = load_module()

    try:
        module.audio_rms_by_frame(Path("missing.mp4"), 0, 1.0)
    except ValueError as exc:
        assert "fps" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ValueError")
