from pr_sentinel.core.enums import FindingCategory, Severity
from pr_sentinel.core.models import Finding
from pr_sentinel.rules.base import BaseRule, RuleContext, RuleMetadata


class PermissionCheckRemovedRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="AUTH_001_PERMISSION_CHECK_REMOVED",
        name="Permission check removed",
        description=(
            "Detects deleted lines that appear to remove permission or "
            "authorization checks."
        ),
        category=FindingCategory.AUTH,
        severity=Severity.HIGH,
    )

    AUTH_TERMS = (
        "haspermission",
        "isauthorized",
        "is_authorized",
        "preauthorize",
        "secured",
        "hasrole",
        "has_role",
        "permission",
        "authorize",
        "authorization",
        "forbidden",
        "accessdenied",
        "access_denied",
    )

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for changed_file in context.changed_files:
            for hunk in changed_file.hunks:
                for line in hunk.lines:
                    if line.line_type != "deleted":
                        continue

                    normalized = line.content.lower().replace(" ", "")

                    if any(term in normalized for term in self.AUTH_TERMS):
                        findings.append(
                            self.build_finding(
                                file_path=changed_file.filename,
                                line_number=line.old_line_no,
                                message=(
                                    "A line related to permission or authorization "
                                    "checks was removed."
                                ),
                                evidence=line.content.strip(),
                                recommendation=(
                                    "Verify that authorization is still enforced and "
                                    "add/update negative authorization tests."
                                ),
                                confidence=0.8,
                            )
                        )

        return findings