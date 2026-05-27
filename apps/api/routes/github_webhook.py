import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from pr_sentinel.core.config import get_settings
from pr_sentinel.core.models import PullRequestInfo
from pr_sentinel.engine.pipeline import AnalysisPipeline
from pr_sentinel.github.client import GitHubClientError
from pr_sentinel.github.comment_publisher import PullRequestCommentPublisher
from pr_sentinel.github.webhook import verify_github_signature
from pr_sentinel.llm.client import LlmClientError
from pr_sentinel.reports.markdown import MarkdownReportGenerator

router = APIRouter(prefix="/api/github", tags=["github-webhook"])

SUPPORTED_PULL_REQUEST_ACTIONS = {
    "opened",
    "reopened",
    "synchronize",
    "ready_for_review",
}


@router.post("/webhook")
async def github_webhook(
    request: Request,
    use_llm: bool = Query(default=False),
    post_comment: bool = Query(default=True),
) -> dict[str, Any]:
    settings = get_settings()
    payload_body = await request.body()

    signature_header = request.headers.get("X-Hub-Signature-256")
    event_name = request.headers.get("X-GitHub-Event")

    if not verify_github_signature(
        payload_body=payload_body,
        signature_header=signature_header,
        secret=settings.github_webhook_secret,
    ):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")

    if event_name != "pull_request":
        return {
            "status": "ignored",
            "reason": f"Unsupported event: {event_name}",
        }

    try:
        payload = json.loads(payload_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    action = payload.get("action")

    if action not in SUPPORTED_PULL_REQUEST_ACTIONS:
        return {
            "status": "ignored",
            "reason": f"Unsupported pull_request action: {action}",
        }

    repo_full_name = payload["repository"]["full_name"]
    pr_number = int(payload["pull_request"]["number"])

    try:
        pull_request = payload_to_minimal_pr_fetch(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
        )
        result = AnalysisPipeline(use_llm=use_llm).analyze(pull_request)

        comment_status: str | None = None

        if post_comment:
            markdown_report = MarkdownReportGenerator().generate(result)
            comment_status = PullRequestCommentPublisher().publish_or_update_comment(
                repo_full_name=repo_full_name,
                pr_number=pr_number,
                markdown_body=markdown_report,
            )

    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LlmClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    risk = result.risk_score

    return {
        "status": "analyzed",
        "repo": repo_full_name,
        "pr": pr_number,
        "action": action,
        "findings_count": len(result.findings),
        "test_recommendations_count": len(result.test_recommendations),
        "risk_score": risk.score if risk else 0,
        "risk_band": risk.band.value if risk else "LOW",
        "deterministic_score": risk.deterministic_score if risk else 0,
        "ai_adjustment": risk.ai_adjustment if risk else 0,
        "comment_status": comment_status,
    }


def payload_to_minimal_pr_fetch(repo_full_name: str, pr_number: int) -> PullRequestInfo:
    from pr_sentinel.github.pr_fetcher import PullRequestFetcher

    return PullRequestFetcher().fetch(
        repo_full_name=repo_full_name,
        pr_number=pr_number,
    )