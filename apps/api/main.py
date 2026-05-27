from fastapi import FastAPI

from apps.api.routes.analysis import router as analysis_router
from apps.api.routes.github_webhook import router as github_webhook_router
from pr_sentinel.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Pull Request Risk Intelligence Platform",
    version="0.1.0",
)

app.include_router(analysis_router)
app.include_router(github_webhook_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
    }