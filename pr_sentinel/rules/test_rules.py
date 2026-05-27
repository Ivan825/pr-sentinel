from pr_sentinel.core.enums import FileCategory, FindingCategory, Severity
from pr_sentinel.core.models import Finding
from pr_sentinel.rules.base import BaseRule, RuleContext, RuleMetadata
from pr_sentinel.testsuggester.mapper import TestRecommendationMapper


class RiskySourceWithoutMatchingTestRule(BaseRule):
    metadata = RuleMetadata(
        rule_id="TEST_001_RISKY_SOURCE_WITHOUT_MATCHING_TEST",
        name="Risky source changed without matching test",
        description=(
            "Detects risky source-code changes where no directly matching test file "
            "was modified in the same PR."
        ),
        category=FindingCategory.TEST,
        severity=Severity.MEDIUM,
    )

    RISKY_CATEGORIES = {
        FileCategory.AUTH,
        FileCategory.SECURITY,
        FileCategory.API,
        FileCategory.DATABASE,
        FileCategory.BACKEND,
    }

    def __init__(self, mapper: TestRecommendationMapper | None = None) -> None:
        self.mapper = mapper or TestRecommendationMapper()

    def evaluate(self, context: RuleContext) -> list[Finding]:
        findings: list[Finding] = []

        changed_paths = {changed_file.filename for changed_file in context.changed_files}

        for changed_file in context.changed_files:
            if FileCategory.TEST in changed_file.categories:
                continue

            if not self.RISKY_CATEGORIES.intersection(changed_file.categories):
                continue

            candidates = self.mapper.candidate_tests_for_file(changed_file.filename)

            if not candidates:
                continue

            matching_tests = [candidate for candidate in candidates if candidate in changed_paths]

            if matching_tests:
                continue

            findings.append(
                self.build_finding(
                    file_path=changed_file.filename,
                    line_number=None,
                    message=(
                        "Risky source file changed, but no directly matching test file "
                        "was modified in this PR."
                    ),
                    evidence=", ".join(candidates[:5]),
                    recommendation=(
                        "Add or update relevant unit/integration tests, or document why "
                        "existing tests already cover this change."
                    ),
                    confidence=0.72,
                )
            )

        return findings