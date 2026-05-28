from pathlib import Path
from typing import Any

from pr_sentinel.github.app_auth import extract_installation_id


def test_extract_installation_id_returns_id_when_present() -> None:
    payload: dict[str, Any] = {
        "installation": {
            "id": 12345,
        }
    }

    assert extract_installation_id(payload) == 12345


def test_extract_installation_id_returns_none_when_missing() -> None:
    payload: dict[str, Any] = {}

    assert extract_installation_id(payload) is None


def test_extract_installation_id_returns_none_when_invalid() -> None:
    payload: dict[str, Any] = {
        "installation": {
            "id": "12345",
        }
    }

    assert extract_installation_id(payload) is None


def test_private_key_file_should_not_exist_in_repo() -> None:
    forbidden_names = {
        "private-key.pem",
        "github-app.pem",
        "prsentinel-app.pem",
    }

    repo_root = Path.cwd()

    for forbidden_name in forbidden_names:
        assert not (repo_root / forbidden_name).exists()