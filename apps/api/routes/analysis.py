from fastapi import APIRouter, HTTPException

from apps.api.schemas import AnalyzePullRequestRequest, AnalyzePullRequestResponse
from pr_sentinel.engine.pipeline import AnalysisPipeline
from pr_sentinel.github.client import GitHubClientError
from pr_sentinel.github.comment_publisher import PullRequestCommentPublisher
from pr_sentinel.github.pr_fetcher import PullRequestFetcher
from pr_sentinel.llm.client import LlmClientError
from pr_sentinel.reports.markdown import MarkdownReportGenerator

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalyzePullRequestResponse)
def analyze_pull_request(request: AnalyzePullRequestRequest) -> AnalyzePullRequestResponse:
    try:
        pull_request = PullRequestFetcher().fetch(
            repo_full_name=request.repo,
            pr_number=request.pr,
        )

        result = AnalysisPipeline(use_llm=request.use_llm).analyze(pull_request)

        comment_status: str | None = None

        if request.post_comment:
            markdown_report = MarkdownReportGenerator().generate(result)
            comment_status = PullRequestCommentPublisher().publish_or_update_comment(
                repo_full_name=request.repo,
                pr_number=request.pr,
                markdown_body=markdown_report,
            )

    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except LlmClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    risk = result.risk_score

    return AnalyzePullRequestResponse(
        repo=request.repo,
        pr=request.pr,
        findings_count=len(result.findings),
        test_recommendations_count=len(result.test_recommendations),
        risk_score=risk.score if risk else 0,
        risk_band=risk.band.value if risk else "LOW",
        deterministic_score=risk.deterministic_score if risk else 0,
        ai_adjustment=risk.ai_adjustment if risk else 0,
        comment_status=comment_status,
        analysis=result.model_dump(mode="json"),
    )