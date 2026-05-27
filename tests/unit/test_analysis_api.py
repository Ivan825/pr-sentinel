from fastapi.testclient import TestClient

from apps.api.main import app
from pr_sentinel.core.enums import FileCategory, FileChangeStatus
from pr_sentinel.core.models import ChangedFile, PullRequestInfo


class FakePullRequestFetcher:
    def fetch(self, repo_full_name: str, pr_number: int) -> PullRequestInfo:
        return PullRequestInfo(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            title="Fake PR",
            author="contributor",
            base_branch="main",
            head_branch="feature",
            changed_files=[
                ChangedFile(
                    filename="src/main/java/com/app/OrderService.java",
                    status=FileChangeStatus.MODIFIED,
                    additions=3,
                    deletions=1,
                    changes=4,
                    language="Java",
                    categories=[FileCategory.BACKEND],
                    hunks=[],
                )
            ],
        )


def test_analyze_api_returns_analysis(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import apps.api.routes.analysis as analysis_route

    monkeypatch.setattr(
        analysis_route,
        "PullRequestFetcher",
        lambda: FakePullRequestFetcher(),
    )

    client = TestClient(app)

    response = client.post(
        "/api/analyze",
        json={
            "repo": "example/repo",
            "pr": 1,
            "use_llm": False,
            "post_comment": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["repo"] == "example/repo"
    assert data["pr"] == 1
    assert data["findings_count"] >= 1
    assert data["risk_score"] > 0