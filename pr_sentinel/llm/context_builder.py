from pr_sentinel.core.enums import Severity
from pr_sentinel.core.models import AnalysisResult, ChangedFile, Finding, TestRecommendation
from pr_sentinel.llm.models import (
    LlmChangedFileContext,
    LlmDiffLine,
    LlmFindingContext,
    LlmReviewContext,
    LlmTestRecommendationContext,
)


class LlmContextBuilder:
    def __init__(
        self,
        max_files: int = 12,
        max_lines_per_file: int = 80,
    ) -> None:
        self.max_files = max_files
        self.max_lines_per_file = max_lines_per_file

    def build(self, result: AnalysisResult) -> LlmReviewContext:
        deterministic_score = result.risk_score.deterministic_score if result.risk_score else 0

        return LlmReviewContext(
            repo_full_name=result.pr.repo_full_name,
            pr_number=result.pr.pr_number,
            pr_title=result.pr.title,
            author=result.pr.author,
            base_branch=result.pr.base_branch,
            head_branch=result.pr.head_branch,
            deterministic_score=deterministic_score,
            deterministic_findings=self._finding_contexts(result.findings),
            test_recommendations=self._test_recommendation_contexts(
                result.test_recommendations
            ),
            changed_files=self._changed_file_contexts(result.pr.changed_files),
            instructions=(
                "Review the PR for semantic risks that deterministic rules may miss. "
                "Only report findings directly supported by the provided diff lines. "
                "Do not invent files, line numbers, behavior, dependencies, or project context."
            ),
        )

    def _finding_contexts(self, findings: list[Finding]) -> list[LlmFindingContext]:
        priority = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }

        sorted_findings = sorted(
            findings,
            key=lambda finding: priority[finding.severity],
        )

        return [
            LlmFindingContext(
                rule_id=finding.rule_id,
                title=finding.title,
                category=finding.category.value,
                severity=finding.severity.value,
                file_path=finding.file_path,
                line_number=finding.line_number,
                message=finding.message,
                evidence=finding.evidence,
                recommendation=finding.recommendation,
                confidence=finding.confidence,
            )
            for finding in sorted_findings
        ]

    def _test_recommendation_contexts(
        self,
        recommendations: list[TestRecommendation],
    ) -> list[LlmTestRecommendationContext]:
        return [
            LlmTestRecommendationContext(
                source_file=recommendation.source_file,
                recommended_tests=recommendation.recommended_tests,
                reason=recommendation.reason,
            )
            for recommendation in recommendations
        ]

    def _changed_file_contexts(
        self,
        changed_files: list[ChangedFile],
    ) -> list[LlmChangedFileContext]:
        prioritized_files = sorted(
            changed_files,
            key=self._file_priority,
            reverse=True,
        )

        contexts: list[LlmChangedFileContext] = []

        for changed_file in prioritized_files[: self.max_files]:
            contexts.append(
                LlmChangedFileContext(
                    filename=changed_file.filename,
                    language=changed_file.language,
                    categories=[category.value for category in changed_file.categories],
                    additions=changed_file.additions,
                    deletions=changed_file.deletions,
                    selected_lines=self._selected_lines(changed_file),
                )
            )

        return contexts

    def _file_priority(self, changed_file: ChangedFile) -> int:
        categories = {category.value for category in changed_file.categories}
        score = changed_file.additions + changed_file.deletions

        if "AUTH" in categories:
            score += 80
        if "SECURITY" in categories:
            score += 80
        if "API" in categories:
            score += 50
        if "DATABASE" in categories:
            score += 45
        if "CONFIG" in categories:
            score += 35
        if "DEPENDENCY" in categories:
            score += 30
        if "TEST" in categories:
            score -= 20
        if "DOCUMENTATION" in categories:
            score -= 50

        return score

    def _selected_lines(self, changed_file: ChangedFile) -> list[LlmDiffLine]:
        lines: list[LlmDiffLine] = []

        for hunk in changed_file.hunks:
            for line in hunk.lines:
                if line.line_type not in {"added", "deleted"}:
                    continue

                lines.append(
                    LlmDiffLine(
                        file_path=changed_file.filename,
                        old_line_no=line.old_line_no,
                        new_line_no=line.new_line_no,
                        line_type=line.line_type,
                        content=line.content,
                    )
                )

                if len(lines) >= self.max_lines_per_file:
                    return lines

        return lines