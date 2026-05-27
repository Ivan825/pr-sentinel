from pr_sentinel.core.enums import FileCategory, FindingCategory, Severity
from pr_sentinel.core.models import Finding
from pr_sentinel.rules.base import BaseRule, RuleContext, RuleMetadata


class DependencyFileChangedRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="DEP_001_DEPENDENCY_FILE_CHANGED",
        name="Dependency file changed",
        description="Flags dependency manifest or lockfile changes for reviewer attention.",
        category=FindingCategory.DEPENDENCY,
        severity=Severity.MEDIUM,
    )

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for changed_file in context.changed_files:
            if FileCategory.DEPENDENCY not in changed_file.categories:
                continue

            findings.append(
                self.build_finding(
                    file_path=changed_file.filename,
                    line_number=None,
                    message="Dependency manifest or lockfile was changed.",
                    evidence=f"+{changed_file.additions} -{changed_file.deletions}",
                    recommendation=(
                        "Review dependency changes for breaking changes, supply-chain risk, "
                        "license changes, and security vulnerabilities."
                    ),
                    confidence=0.75,
                )
            )

        return findings