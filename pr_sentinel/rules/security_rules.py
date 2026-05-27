import re

from pr_sentinel.core.enums import FindingCategory, Severity
from pr_sentinel.core.models import Finding
from pr_sentinel.rules.base import BaseRule, RuleContext, RuleMetadata

SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    (
        "Generic API key assignment",
        re.compile(r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]{12,}['\"]"),
    ),
    ("Private key header", re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----")),
]


class HardcodedSecretRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="SEC_001_HARDCODED_SECRET",
        name="Hardcoded secret detected",
        description="Detects secret-like values added in a pull request.",
        category=FindingCategory.SECURITY,
        severity=Severity.CRITICAL,
    )

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for changed_file in context.changed_files:
            for hunk in changed_file.hunks:
                for line in hunk.lines:
                    if line.line_type != "added":
                        continue

                    for secret_type, pattern in SECRET_PATTERNS:
                        if not pattern.search(line.content):
                            continue

                        findings.append(
                            self.build_finding(
                                file_path=changed_file.filename,
                                line_number=line.new_line_no,
                                message=f"Potential {secret_type} was added.",
                                evidence=line.content.strip(),
                                recommendation=(
                                    "Remove the secret from code, rotate it if it is real, "
                                    "and use environment variables or a secret manager."
                                ),
                                confidence=0.9,
                            )
                        )

                        break

        return findings


class RawSqlConcatenationRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="SEC_002_RAW_SQL_CONCATENATION",
        name="Raw SQL string concatenation detected",
        description="Detects added SQL queries that appear to concatenate user-controlled values.",
        category=FindingCategory.SECURITY,
        severity=Severity.HIGH,
    )

    SQL_KEYWORDS = ("select ", "insert ", "update ", "delete ")

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        for changed_file in context.changed_files:
            for hunk in changed_file.hunks:
                for line in hunk.lines:
                    if line.line_type != "added":
                        continue

                    lowered = line.content.lower()

                    contains_sql = any(keyword in lowered for keyword in self.SQL_KEYWORDS)
                    contains_concat = (
                        '" +' in line.content
                        or '+ "' in line.content
                        or "' +" in line.content
                        or "+ '" in line.content
                    )

                    if contains_sql and contains_concat:
                        findings.append(
                            self.build_finding(
                                file_path=changed_file.filename,
                                line_number=line.new_line_no,
                                message="Raw SQL appears to be built using string concatenation.",
                                evidence=line.content.strip(),
                                recommendation=(
                                    "Use parameterized queries or prepared statements instead of "
                                    "concatenating values into SQL strings."
                                ),
                                confidence=0.82,
                            )
                        )

        return findings