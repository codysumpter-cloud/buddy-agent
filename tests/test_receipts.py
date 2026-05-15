import json

from buddy_agent.receipts import ReceiptRecord, ReceiptWriter, sanitize_json
from buddy_agent.runtime import RuntimeEngine


def test_receipt_writer_writes_jsonl_and_redacts_sensitive_keys(tmp_path):
    writer = ReceiptWriter(tmp_path)
    record = ReceiptRecord(
        action="test.action",
        status="ok",
        summary="safe summary",
        metadata={
            "api_key": "not-a-real-key",
            "nested": {"token": "not-a-real-token"},
            "safe": "value",
        },
    )

    path = writer.write(record)

    payload = json.loads(path.read_text(encoding="utf-8").strip())
    assert payload["summary"] == "safe summary"
    assert payload["metadata"]["api_key"] == "[redacted]"
    assert payload["metadata"]["nested"]["token"] == "[redacted]"
    assert payload["metadata"]["safe"] == "value"


def test_sanitize_json_redacts_by_value_marker():
    assert sanitize_json("value contains github_pat_placeholder") == "[redacted]"


def test_runtime_receipt_does_not_record_prompt_content(tmp_path):
    writer = ReceiptWriter(tmp_path)
    engine = RuntimeEngine(session_id="receipt-test", receipt_writer=writer)

    engine.receive("private prompt content")

    payload = json.loads(next(tmp_path.glob("*.jsonl")).read_text(encoding="utf-8"))
    assert "private prompt content" not in json.dumps(payload)
    assert payload["metadata"]["input_length"] > 0
