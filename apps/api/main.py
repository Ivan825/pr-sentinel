from fastapi import FastAPI

from pr_sentinel.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Pull Request Risk Intelligence Platform",
    version="0.1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
    }