"""Local receipt writer with conservative sanitization."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from .record import JSONValue, ReceiptRecord

DEFAULT_RECEIPTS_DIR = Path(
    os.getenv("BUDDY_RECEIPTS_DIR", "~/.buddy_agent/receipts")
).expanduser()
SENSITIVE_KEY_PARTS = (
    "secret",
    "token",
    "password",
    "cookie",
    "authorization",
    "api_key",
    "apikey",
    "private_key",
    "oauth",
    "account_id",
    "credential",
)
SENSITIVE_VALUE_MARKERS = (
    "sk-",
    "ghp_",
    "github_pat_",
    "-----BEGIN",
    "xoxb-",
    "xoxp-",
)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def sanitize_json(value: JSONValue, *, key: str = "") -> JSONValue:
    """Redact sensitive-looking JSON values by key or obvious token marker."""
    if key and _is_sensitive_key(key):
        return "[redacted]"
    if isinstance(value, dict):
        return {
            item_key: sanitize_json(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if isinstance(value, str) and any(marker in value for marker in SENSITIVE_VALUE_MARKERS):
        return "[redacted]"
    return value


def sanitize_record(record: ReceiptRecord) -> dict[str, JSONValue]:
    """Return a sanitized receipt payload."""
    return cast(dict[str, JSONValue], sanitize_json(record.to_dict()))


class ReceiptWriter:
    """Write local JSONL or JSON receipt files."""

    def __init__(self, directory: Path | None = None, *, jsonl: bool = True) -> None:
        self.directory = directory or DEFAULT_RECEIPTS_DIR
        self.jsonl = jsonl

    def path(self) -> Path:
        """Return the configured receipt directory."""
        return self.directory

    def write(self, record: ReceiptRecord) -> Path:
        """Write one sanitized receipt record and return the file path."""
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = sanitize_record(record)
        if self.jsonl:
            path = self.directory / f"{datetime.now(UTC).date().isoformat()}.jsonl"
            with path.open("a", encoding="utf-8") as receipt_file:
                receipt_file.write(json.dumps(payload, sort_keys=True) + "\n")
            return path
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.directory / f"receipt-{timestamp}.json"
        content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        path.write_text(content, encoding="utf-8")
        return path
