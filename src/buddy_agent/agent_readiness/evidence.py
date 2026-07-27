"""Bundle verification, security, and economics into existing Buddy receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from buddy_agent.receipts import JSONValue, ReceiptRecord, ReceiptStatus

from .economics import TaskEconomics
from .security import SecurityGateResult


@dataclass(frozen=True)
class TaskEvidenceBundle:
    action: str
    summary: str
    economics: TaskEconomics
    security: SecurityGateResult
    checks: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()

    def to_receipt(self) -> ReceiptRecord:
        status: ReceiptStatus
        if self.security.decision == "block":
            status = "deny"
        elif self.security.decision == "review" or not self.economics.verified_completion:
            status = "review"
        else:
            status = "ok"
        return ReceiptRecord(
            action=self.action,
            status=status,
            summary=self.summary,
            metadata=cast(
                dict[str, JSONValue],
                {
                    "economics": self.economics.receipt_metadata(),
                    "security": self.security.to_dict(),
                    "checks": list(self.checks),
                    "artifacts": list(self.artifacts),
                },
            ),
        )
