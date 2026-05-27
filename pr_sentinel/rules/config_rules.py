from pr_sentinel.core.enums import FindingCategory, Severity
from pr_sentinel.core.models import Finding
from pr_sentinel.rules.base import BaseRule, RuleContext, RuleMetadata


class CorsWildcardRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="CFG_001_CORS_WILDCARD_ENABLED",
        name="CORS wildcard enabled",
        description="Detects newly added permissive CORS wildcard configuration.",
        category=FindingCategory.CONFIG,
        severity=Severity.HIGH,
    )

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        suspicious_patterns = (
            "allowed-origins: '*'",
            "allowed_origins: '*'",
            "allowedorigins=*",
            "cors.allowed-origins=*",
            "origin: '*'",
            "origins: ['*']",
            "allow_origins=[\"*\"]",
            "allow_origins=['*']",
        )

        for changed_file in context.changed_files:
            for hunk in changed_file.hunks:
                for line in hunk.lines:
                    if line.line_type != "added":
                        continue

                    normalized = line.content.lower().replace(" ", "")

                    wildcard_added = any(
                        pattern.replace(" ", "") in normalized
                        for pattern in suspicious_patterns
                    )

                    if wildcard_added:
                        findings.append(
                            self.build_finding(
                                file_path=changed_file.filename,
                                line_number=line.new_line_no,
                                message="A permissive CORS wildcard appears to have been added.",
                                evidence=line.content.strip(),
                                recommendation=(
                                    "Avoid wildcard CORS in production. Restrict allowed origins "
                                    "to trusted frontend domains."
                                ),
                                confidence=0.84,
                            )
                        )

        return findings


class DebugModeEnabledRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="CFG_002_DEBUG_MODE_ENABLED",
        name="Debug mode enabled",
        description="Detects newly added debug mode configuration.",
        category=FindingCategory.CONFIG,
        severity=Severity.MEDIUM,
    )

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        debug_patterns = (
            "debug=true",
            "debug: true",
            "app_debug=true",
            "flask_debug=1",
            "spring.jpa.show-sql=true",
        )

        for changed_file in context.changed_files:
            for hunk in changed_file.hunks:
                for line in hunk.lines:
                    if line.line_type != "added":
                        continue

                    normalized = line.content.lower().strip().replace(" ", "")

                    debug_added = any(
                        pattern.replace(" ", "") in normalized for pattern in debug_patterns
                    )

                    if debug_added:
                        findings.append(
                            self.build_finding(
                                file_path=changed_file.filename,
                                line_number=line.new_line_no,
                                message="Debug-style configuration appears to have been enabled.",
                                evidence=line.content.strip(),
                                recommendation=(
                                    "Ensure debug settings are disabled in production environments."
                                ),
                                confidence=0.78,
                            )
                        )

        return findings