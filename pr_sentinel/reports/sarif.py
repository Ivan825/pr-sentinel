import json
from collections import defaultdict
from typing import Any

from pr_sentinel.core.models import AnalysisResult, Finding

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"


class SarifReportGenerator:
    def generate_dict(self, result: AnalysisResult) -> dict[str, Any]:
        rules = self._build_rules(result.findings)
        sarif_results = [self._finding_to_result(finding) for finding in result.findings]

        return {
            "$schema": SARIF_SCHEMA,
            "version": SARIF_VERSION,
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "PRSentinel",
                            "informationUri": "https://github.com",
                            "rules": rules,
                        }
                    },
                    "results": sarif_results,
                    "properties": {
                        "repository": result.pr.repo_full_name,
                        "pullRequest": result.pr.pr_number,
                        "pullRequestTitle": result.pr.title,
                        "author": result.pr.author,
                        "baseBranch": result.pr.base_branch,
                        "headBranch": result.pr.head_branch,
                        "riskScore": result.risk_score.score if result.risk_score else 0,
                        "riskBand": result.risk_score.band.value
                        if result.risk_score
                        else "LOW",
                        "deterministicScore": result.risk_score.deterministic_score
                        if result.risk_score
                        else 0,
                        "aiAdjustment": result.risk_score.ai_adjustment
                        if result.risk_score
                        else 0,
                    },
                }
            ],
        }

    def generate_json(self, result: AnalysisResult, indent: int = 2) -> str:
        return json.dumps(
            self.generate_dict(result),
            indent=indent,
            ensure_ascii=False,
        )

    def _build_rules(self, findings: list[Finding]) -> list[dict[str, Any]]:
        grouped: dict[str, list[Finding]] = defaultdict(list)

        for finding in findings:
            grouped[finding.rule_id].append(finding)

        rules: list[dict[str, Any]] = []

        for rule_id, rule_findings in sorted(grouped.items()):
            first = rule_findings[0]

            rules.append(
                {
                    "id": rule_id,
                    "name": first.title,
                    "shortDescription": {
                        "text": first.title,
                    },
                    "fullDescription": {
                        "text": first.message,
                    },
                    "defaultConfiguration": {
                        "level": self._severity_to_sarif_level(first.severity.value),
                    },
                    "properties": {
                        "category": first.category.value,
                        "source": first.source,
                    },
                }
            )

        return rules

    def _finding_to_result(self, finding: Finding) -> dict[str, Any]:
        physical_location: dict[str, Any] = {
            "artifactLocation": {
                "uri": finding.file_path,
            }
        }

        if finding.line_number is not None:
            physical_location["region"] = {
                "startLine": max(finding.line_number, 1),
            }

        return {
            "ruleId": finding.rule_id,
            "level": self._severity_to_sarif_level(finding.severity.value),
            "message": {
                "text": finding.message,
            },
            "locations": [
                {
                    "physicalLocation": physical_location,
                }
            ],
            "properties": {
                "title": finding.title,
                "category": finding.category.value,
                "severity": finding.severity.value,
                "source": finding.source,
                "confidence": finding.confidence,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
            },
        }

    def _severity_to_sarif_level(self, severity: str) -> str:
        if severity in {"CRITICAL", "HIGH"}:
            return "error"

        if severity == "MEDIUM":
            return "warning"

        return "note"