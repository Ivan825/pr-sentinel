from typing import Any

from pr_sentinel.core.enums import FindingCategory, Severity
from pr_sentinel.core.models import AnalysisResult, Finding
from pr_sentinel.llm.client import LlmClient
from pr_sentinel.llm.context_builder import LlmContextBuilder
from pr_sentinel.llm.models import AiSemanticFinding, LlmReviewResult


class SemanticReviewer:
    VALID_CATEGORIES = {category.value for category in FindingCategory}
    VALID_SEVERITIES = {severity.value for severity in Severity}
    MIN_ACCEPTED_CONFIDENCE = 0.55

    CATEGORY_ALIASES = {
        "AUTHORIZATION": "AUTH",
        "AUTHENTICATION": "AUTH",
        "PERMISSION": "AUTH",
        "PERMISSIONS": "AUTH",
        "ACCESS_CONTROL": "AUTH",
        "ACCESS CONTROL": "AUTH",
        "VALIDATION": "API",
        "API_CONTRACT": "API",
        "API CONTRACT": "API",
        "DB": "DATABASE",
        "SQL": "DATABASE",
        "DATA": "DATABASE",
        "SECRET": "SECURITY",
        "SECRETS": "SECURITY",
        "CREDENTIAL": "SECURITY",
        "CREDENTIALS": "SECURITY",
        "CONFIGURATION": "CONFIG",
        "DEPENDENCIES": "DEPENDENCY",
        "CI": "INFRA",
        "CD": "INFRA",
        "DEVOPS": "INFRA",
        "TESTING": "TEST",
    }

    DUPLICATE_TEST_KEYWORDS = (
        "missing test",
        "without matching test",
        "no matching test",
        "no test",
        "add test",
        "add a test",
        "add tests",
        "unit test",
        "integration test",
        "test coverage",
        "not covered by tests",
    )

    def __init__(
        self,
        context_builder: LlmContextBuilder | None = None,
        llm_client: LlmClient | None = None,
    ) -> None:
        self.context_builder = context_builder or LlmContextBuilder()
        self.llm_client = llm_client or LlmClient()

    def review(self, result: AnalysisResult) -> LlmReviewResult:
        context = self.context_builder.build(result)
        raw_response = self.llm_client.review(context.model_dump(mode="json"))
        normalized_response = self._normalize_response(raw_response)

        parsed = LlmReviewResult.model_validate(normalized_response)
        validated_findings = [
            finding
            for finding in parsed.findings
            if self._is_valid_ai_finding(result, finding)
        ]

        return LlmReviewResult(
            findings=validated_findings,
            ai_adjustment=parsed.ai_adjustment if validated_findings else 0,
            ai_adjustment_reasons=parsed.ai_adjustment_reasons if validated_findings else [],
        )

    def to_core_findings(self, review_result: LlmReviewResult) -> list[Finding]:
        findings: list[Finding] = []

        for index, ai_finding in enumerate(review_result.findings, start=1):
            findings.append(
                Finding(
                    rule_id=f"AI_SEMANTIC_{index:03d}",
                    title=ai_finding.title,
                    category=ai_finding.category,
                    severity=ai_finding.severity,
                    file_path=ai_finding.file_path,
                    line_number=ai_finding.line_number,
                    message=ai_finding.message,
                    evidence=ai_finding.evidence,
                    recommendation=ai_finding.recommendation,
                    confidence=ai_finding.confidence,
                    source="AI_ASSISTED",
                )
            )

        return findings

    def _normalize_response(self, raw_response: dict[str, Any]) -> dict[str, Any]:
        findings = raw_response.get("findings", [])

        if not isinstance(findings, list):
            raw_response["findings"] = []
            return raw_response

        normalized_findings: list[dict[str, Any]] = []

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            normalized = finding.copy()
            normalized["category"] = self._normalize_category(normalized.get("category"))
            normalized["severity"] = self._normalize_severity(normalized.get("severity"))
            normalized["confidence"] = self._normalize_confidence(
                normalized.get("confidence")
            )

            if normalized["category"] is None or normalized["severity"] is None:
                continue

            normalized_findings.append(normalized)

        raw_response["findings"] = normalized_findings
        raw_response["ai_adjustment"] = self._normalize_ai_adjustment(
            raw_response.get("ai_adjustment")
        )

        reasons = raw_response.get("ai_adjustment_reasons", [])
        raw_response["ai_adjustment_reasons"] = reasons if isinstance(reasons, list) else []

        return raw_response

    def _normalize_category(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None

        cleaned = value.strip().upper()

        if cleaned in self.VALID_CATEGORIES:
            return cleaned

        if cleaned in self.CATEGORY_ALIASES:
            return self.CATEGORY_ALIASES[cleaned]

        for separator in ("|", "/", ",", "&", " AND "):
            if separator in cleaned:
                parts = [part.strip() for part in cleaned.split(separator)]

                for part in parts:
                    if part in self.VALID_CATEGORIES:
                        return part
                    if part in self.CATEGORY_ALIASES:
                        return self.CATEGORY_ALIASES[part]

        for category in self.VALID_CATEGORIES:
            if category in cleaned:
                return category

        return None

    def _normalize_severity(self, value: object) -> str | None:
        if not isinstance(value, str):
            return None

        cleaned = value.strip().upper()

        if cleaned in self.VALID_SEVERITIES:
            return cleaned

        return None

    def _normalize_confidence(self, value: object) -> float:
        if isinstance(value, int | float):
            return min(max(float(value), 0.0), 1.0)

        return 0.0

    def _normalize_ai_adjustment(self, value: object) -> int:
        if not isinstance(value, int):
            return 0

        return min(max(value, -10), 20)

    def _is_valid_ai_finding(
        self,
        result: AnalysisResult,
        finding: AiSemanticFinding,
    ) -> bool:
        if finding.confidence < self.MIN_ACCEPTED_CONFIDENCE:
            return False

        if not self._is_evidence_backed(
            result=result,
            file_path=finding.file_path,
            line_number=finding.line_number,
        ):
            return False

        if self._looks_like_low_value_comment_finding(finding):
            return False

        return not self._duplicates_deterministic_finding(result, finding)

    def _duplicates_deterministic_finding(
        self,
        result: AnalysisResult,
        finding: AiSemanticFinding,
    ) -> bool:
        if self._is_test_gap_finding(finding):
            return self._deterministic_test_gap_exists_for_file(result, finding.file_path)

        return self._same_category_same_file_same_theme_exists(result, finding)

    def _is_test_gap_finding(self, finding: AiSemanticFinding) -> bool:
        text = " ".join(
            [
                finding.title,
                finding.message,
                finding.evidence,
                finding.recommendation,
            ]
        ).lower()

        return finding.category == FindingCategory.TEST or any(
            keyword in text for keyword in self.DUPLICATE_TEST_KEYWORDS
        )

    def _deterministic_test_gap_exists_for_file(
        self,
        result: AnalysisResult,
        file_path: str,
    ) -> bool:
        for deterministic_finding in result.findings:
            if deterministic_finding.source != "DETERMINISTIC":
                continue

            if deterministic_finding.file_path != file_path:
                continue

            if deterministic_finding.rule_id == "TEST_001_RISKY_SOURCE_WITHOUT_MATCHING_TEST":
                return True

            deterministic_text = " ".join(
                [
                    deterministic_finding.title,
                    deterministic_finding.message,
                    deterministic_finding.evidence or "",
                    deterministic_finding.recommendation or "",
                ]
            ).lower()

            if any(keyword in deterministic_text for keyword in self.DUPLICATE_TEST_KEYWORDS):
                return True

        for recommendation in result.test_recommendations:
            if recommendation.source_file != file_path:
                continue

            recommendation_text = " ".join(
                [
                    recommendation.reason,
                    " ".join(recommendation.recommended_tests),
                ]
            ).lower()

            if any(keyword in recommendation_text for keyword in self.DUPLICATE_TEST_KEYWORDS):
                return True

        return False

    def _same_category_same_file_same_theme_exists(
        self,
        result: AnalysisResult,
        finding: AiSemanticFinding,
    ) -> bool:
        ai_text = self._normalize_text(
            " ".join(
                [
                    finding.title,
                    finding.message,
                    finding.evidence,
                    finding.recommendation,
                ]
            )
        )

        if not ai_text:
            return False

        for deterministic_finding in result.findings:
            if deterministic_finding.source != "DETERMINISTIC":
                continue

            if deterministic_finding.file_path != finding.file_path:
                continue

            if deterministic_finding.category != finding.category:
                continue

            deterministic_text = self._normalize_text(
                " ".join(
                    [
                        deterministic_finding.title,
                        deterministic_finding.message,
                        deterministic_finding.evidence or "",
                        deterministic_finding.recommendation or "",
                    ]
                )
            )

            if self._jaccard_similarity(ai_text, deterministic_text) >= 0.55:
                return True

        return False

    def _normalize_text(self, text: str) -> set[str]:
        stop_words = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "be",
            "by",
            "for",
            "from",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "that",
            "the",
            "this",
            "to",
            "was",
            "were",
            "with",
        }

        cleaned_tokens: set[str] = set()

        for raw_token in text.lower().replace("_", " ").replace("-", " ").split():
            token = "".join(character for character in raw_token if character.isalnum())

            if not token or token in stop_words or len(token) <= 2:
                continue

            cleaned_tokens.add(token)

        return cleaned_tokens

    def _jaccard_similarity(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0

        return len(left.intersection(right)) / len(left.union(right))

    def _looks_like_low_value_comment_finding(self, finding: AiSemanticFinding) -> bool:
        evidence = finding.evidence.strip().lower()
        message = finding.message.strip().lower()

        comment_only = evidence.startswith("//") or evidence.startswith("#")
        claims_sensitive_data = (
            "sensitive data" in message
            or "secret" in message
            or "credential" in message
        )

        has_known_secret_signal = any(
            signal in evidence
            for signal in (
                "api_key",
                "apikey",
                "secret",
                "token",
                "password",
                "ghp_",
                "akia",
                "private key",
            )
        )

        return comment_only and claims_sensitive_data and not has_known_secret_signal

    def _is_evidence_backed(
        self,
        result: AnalysisResult,
        file_path: str,
        line_number: int | None,
    ) -> bool:
        changed_file = next(
            (file for file in result.pr.changed_files if file.filename == file_path),
            None,
        )

        if changed_file is None:
            return False

        if line_number is None:
            return True

        for hunk in changed_file.hunks:
            for line in hunk.lines:
                if line.line_type not in {"added", "deleted"}:
                    continue

                if line.new_line_no == line_number or line.old_line_no == line_number:
                    return True

        return False