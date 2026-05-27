from abc import ABC, abstractmethod
from dataclasses import dataclass

from pr_sentinel.core.enums import FindingCategory, Severity
from pr_sentinel.core.models import ChangedFile, Finding, PullRequestInfo


@dataclass(frozen=True)
class RuleMetadata:
    rule_id: str
    name: str
    description: str
    category: FindingCategory
    severity: Severity


@dataclass(frozen=True)
class RuleContext:
    pull_request: PullRequestInfo
    changed_files: list[ChangedFile]


class BaseRule(ABC):
    metadata: RuleMetadata

    @abstractmethod
    def evaluate(self, context: RuleContext) -> list[Finding]:
        """Evaluate the rule and return findings."""
        raise NotImplementedError

    def build_finding(
        self,
        file_path: str,
        message: str,
        line_number: int | None = None,
        evidence: str | None = None,
        recommendation: str | None = None,
        confidence: float = 1.0,
    ) -> Finding:
        return Finding(
            rule_id=self.metadata.rule_id,
            title=self.metadata.name,
            category=self.metadata.category,
            severity=self.metadata.severity,
            file_path=file_path,
            line_number=line_number,
            message=message,
            evidence=evidence,
            recommendation=recommendation,
            confidence=confidence,
            source="DETERMINISTIC",
        )