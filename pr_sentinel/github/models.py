from pydantic import BaseModel, Field


class GitHubPullRequest(BaseModel):
    repo_full_name: str
    number: int
    title: str
    author: str
    base_branch: str
    head_branch: str
    html_url: str | None = None


class GitHubChangedFile(BaseModel):
    filename: str
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    patch: str | None = None
    previous_filename: str | None = None
    raw: dict[str, object] = Field(default_factory=dict)