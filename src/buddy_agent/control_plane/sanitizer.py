"""Sanitization helpers for Buddy control-plane receipts.

The sanitizer is intentionally conservative. It redacts common secret-bearing
keys and token-like values, and it rejects values that look like raw prompts,
raw trace dumps, private local paths, browser/session data, or tokenized MCP
URLs before they can become Knowledge Vault receipts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import copy
import re
from typing import Any, Mapping


class SanitizationError(ValueError):
    """Raised when data is too sensitive to safely emit as a receipt."""


SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|authorization|bearer|client[_-]?secret|cookie|credential|jwt|oauth|password|private[_-]?key|secret|token)",
    re.IGNORECASE,
)
TOKEN_VALUE_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|Bearer\s+[A-Za-z0-9._-]{12,})",
    re.IGNORECASE,
)
TOKENIZED_URL_RE = re.compile(r"https?://[^\s]+[?&](token|access_token|api_key|key|secret)=", re.IGNORECASE)
PRIVATE_PATH_RE = re.compile(r"(/Users/[^\s]+|/home/[^\s]+|C:\\Users\\[^\s]+|/var/folders/[^\s]+)")
RAW_TRACE_MARKERS = (
    "resourceSpans",
    "scopeSpans",
    "traceId",
    "spanId",
    "parentSpanId",
    "otel",
    "opentelemetry",
)
RAW_TRACE_KEYS = {marker.lower() for marker in RAW_TRACE_MARKERS} | {"trace", "span", "spans", "raw_trace"}
RAW_PROMPT_KEYS = {"prompt", "raw_prompt", "system_prompt", "developer_prompt", "messages", "conversation", "transcript"}
BROWSER_KEYS = {"browser_session", "cookie", "cookies", "headers", "screenshot", "dom", "page_dump"}


@dataclass(frozen=True)
class SanitizationReport:
    """Public-safe summary of what the sanitizer did."""

    redacted_fields: tuple[str, ...] = field(default_factory=tuple)
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ok(self) -> bool:
        return not self.blocked_reasons


class Sanitizer:
    """Build public-safe values for durable Buddy receipts."""

    redaction_token = "[REDACTED]"

    def sanitize(self, value: Any) -> tuple[Any, SanitizationReport]:
        redacted: list[str] = []
        blocked: list[str] = []
        sanitized = self._sanitize(copy.deepcopy(value), path="$", redacted=redacted, blocked=blocked)
        report = SanitizationReport(tuple(sorted(set(redacted))), tuple(sorted(set(blocked))))
        if not report.ok:
            raise SanitizationError("Unsafe receipt data: " + ", ".join(report.blocked_reasons))
        return sanitized, report

    def assert_safe(self, value: Any) -> SanitizationReport:
        _, report = self.sanitize(value)
        return report

    def _sanitize(self, value: Any, *, path: str, redacted: list[str], blocked: list[str]) -> Any:
        if isinstance(value, Mapping):
            cleaned: dict[str, Any] = {}
            for raw_key, raw_item in value.items():
                key = str(raw_key)
                key_l = key.lower()
                item_path = f"{path}.{key}"

                if key_l in RAW_PROMPT_KEYS:
                    blocked.append(f"raw prompt/conversation field at {item_path}")
                    continue
                if key_l in RAW_TRACE_KEYS:
                    blocked.append(f"raw trace field at {item_path}")
                    continue
                if key_l in BROWSER_KEYS:
                    blocked.append(f"browser/session field at {item_path}")
                    continue
                if SECRET_KEY_RE.search(key):
                    cleaned[key] = self.redaction_token
                    redacted.append(item_path)
                    continue

                cleaned[key] = self._sanitize(raw_item, path=item_path, redacted=redacted, blocked=blocked)
            return cleaned

        if isinstance(value, list):
            return [self._sanitize(item, path=f"{path}[{idx}]", redacted=redacted, blocked=blocked) for idx, item in enumerate(value)]

        if isinstance(value, tuple):
            return tuple(self._sanitize(item, path=f"{path}[{idx}]", redacted=redacted, blocked=blocked) for idx, item in enumerate(value))

        if isinstance(value, str):
            if any(marker.lower() in value.lower() for marker in RAW_TRACE_MARKERS):
                blocked.append(f"raw trace marker at {path}")
                return self.redaction_token
            if TOKENIZED_URL_RE.search(value):
                redacted.append(path)
                return TOKENIZED_URL_RE.sub("https://[REDACTED]", value)
            if TOKEN_VALUE_RE.search(value):
                redacted.append(path)
                return TOKEN_VALUE_RE.sub(self.redaction_token, value)
            if PRIVATE_PATH_RE.search(value):
                redacted.append(path)
                return PRIVATE_PATH_RE.sub("[PRIVATE_PATH]", value)
            return value

        return value
