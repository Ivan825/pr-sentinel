import json

from pr_sentinel.core.models import AnalysisResult


class JsonReportGenerator:
    def generate_dict(self, result: AnalysisResult) -> dict[str, object]:
        return result.model_dump(mode="json")

    def generate_json(self, result: AnalysisResult, indent: int = 2) -> str:
        return json.dumps(
            self.generate_dict(result),
            indent=indent,
            ensure_ascii=False,
        )