from pr_sentinel.core.config import get_settings


def test_settings_loads_app_name() -> None:
    settings = get_settings()

    assert settings.app_name == "PRSentinel"