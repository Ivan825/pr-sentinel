from typing import Any

import httpx

from pr_sentinel.core.config import get_settings


class GitHubClientError(Exception):
    pass


class GitHubClient:
    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        self.token = token if token is not None else settings.github_token
        self.base_url = "https://api.github.com"

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "PRSentinel/0.1.0",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, json_body: dict[str, Any] | None = None) -> Any:
        return self._request("POST", path, json_body=json_body or {})

    def patch(self, path: str, json_body: dict[str, Any]) -> Any:
        return self._request("PATCH", path, json_body=json_body)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"

        try:
            with httpx.Client(timeout=30.0, headers=self._headers()) as client:
                response = client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                )
        except httpx.HTTPError as exc:
            raise GitHubClientError(f"GitHub request failed: {exc}") from exc

        if response.status_code >= 400:
            raise GitHubClientError(
                f"GitHub API error {response.status_code}: {response.text}"
            )

        if not response.content:
            return None

        return response.json()

    def get_paginated(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        per_page: int = 100,
        max_pages: int = 10,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page = 1

        base_params = params.copy() if params else {}
        base_params["per_page"] = per_page

        while page <= max_pages:
            request_params = base_params.copy()
            request_params["page"] = page

            data = self.get(path, params=request_params)

            if not isinstance(data, list):
                raise GitHubClientError("Expected paginated GitHub response to be a list")

            all_items.extend(data)

            if len(data) < per_page:
                break

            page += 1

        return all_items