import base64
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import jwt
from pydantic import BaseModel

from pr_sentinel.core.config import get_settings
from pr_sentinel.github.client import GitHubClient, GitHubClientError


class GitHubAppAuthError(Exception):
    pass


class InstallationToken(BaseModel):
    token: str
    expires_at: str | None = None


class GitHubAppAuthenticator:
    def __init__(
        self,
        app_id: str | None = None,
        private_key_path: str | None = None,
        private_key_base64: str | None = None,
    ) -> None:
        settings = get_settings()
        self.app_id = app_id or settings.github_app_id
        self.private_key_path = private_key_path or settings.github_app_private_key_path
        self.private_key_base64 = (
            private_key_base64 or settings.github_app_private_key_base64
        )

    def create_app_jwt(self) -> str:
        if not self.app_id:
            raise GitHubAppAuthError("GITHUB_APP_ID is missing")

        private_key = self._load_private_key()

        now = datetime.now(UTC)
        payload = {
            "iat": int((now - timedelta(seconds=60)).timestamp()),
            "exp": int((now + timedelta(minutes=9)).timestamp()),
            "iss": self.app_id,
        }

        encoded = jwt.encode(
            payload,
            private_key,
            algorithm="RS256",
        )

        if not isinstance(encoded, str):
            raise GitHubAppAuthError("Failed to generate GitHub App JWT")

        return encoded

    def create_installation_token(self, installation_id: int) -> InstallationToken:
        app_jwt = self.create_app_jwt()
        app_client = GitHubClient(token=app_jwt)

        response = app_client.post(
            f"/app/installations/{installation_id}/access_tokens",
            json_body={},
        )

        if not isinstance(response, dict):
            raise GitHubClientError("Unexpected installation token response")

        token = response.get("token")

        if not isinstance(token, str) or not token:
            raise GitHubClientError("Installation token missing from GitHub response")

        expires_at = response.get("expires_at")

        return InstallationToken(
            token=token,
            expires_at=expires_at if isinstance(expires_at, str) else None,
        )

    def create_installation_client(self, installation_id: int) -> GitHubClient:
        installation_token = self.create_installation_token(installation_id)
        return GitHubClient(token=installation_token.token)

    def _load_private_key(self) -> str:
        if self.private_key_base64:
            try:
                decoded = base64.b64decode(self.private_key_base64).decode("utf-8")
            except Exception as exc:
                raise GitHubAppAuthError(
                    "GITHUB_APP_PRIVATE_KEY_BASE64 is not valid base64"
                ) from exc

            if "BEGIN" not in decoded or "PRIVATE KEY" not in decoded:
                raise GitHubAppAuthError(
                    "GITHUB_APP_PRIVATE_KEY_BASE64 did not decode to a private key"
                )

            return decoded

        if not self.private_key_path:
            raise GitHubAppAuthError(
                "Either GITHUB_APP_PRIVATE_KEY_PATH or "
                "GITHUB_APP_PRIVATE_KEY_BASE64 is required"
            )

        path = Path(self.private_key_path).expanduser()

        if not path.exists():
            raise GitHubAppAuthError(f"GitHub App private key not found: {path}")

        return path.read_text(encoding="utf-8")


def extract_installation_id(payload: dict[str, Any]) -> int | None:
    installation = payload.get("installation")

    if not isinstance(installation, dict):
        return None

    installation_id = installation.get("id")

    if isinstance(installation_id, int):
        return installation_id

    return None