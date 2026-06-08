from pathlib import Path


def test_readme_documents_public_safe_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    for command in (
        "buddy --version",
        "buddy doctor",
        "buddy status",
        "buddy smoke",
        "buddy alpha",
        "buddy skills validate",
        "buddy providers list",
        "buddy receipts path",
        "buddy parity",
    ):
        assert command in readme


def test_readme_does_not_claim_finished_operator() -> None:
    readme = Path("README.md").read_text(encoding="utf-8").lower()

    assert "runnable alpha" in readme
    assert "finished autonomous production operator" in readme
