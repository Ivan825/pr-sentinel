import hashlib
import hmac

from pr_sentinel.github.webhook import verify_github_signature


def test_verify_github_signature_returns_true_when_secret_disabled() -> None:
    assert verify_github_signature(
        payload_body=b'{"hello":"world"}',
        signature_header=None,
        secret=None,
    )


def test_verify_github_signature_accepts_valid_signature() -> None:
    secret = "test-secret"
    payload = b'{"action":"opened"}'

    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    signature = f"sha256={digest}"

    assert verify_github_signature(
        payload_body=payload,
        signature_header=signature,
        secret=secret,
    )


def test_verify_github_signature_rejects_invalid_signature() -> None:
    assert not verify_github_signature(
        payload_body=b'{"action":"opened"}',
        signature_header="sha256=invalid",
        secret="test-secret",
    )


def test_verify_github_signature_rejects_missing_signature_when_secret_enabled() -> None:
    assert not verify_github_signature(
        payload_body=b'{"action":"opened"}',
        signature_header=None,
        secret="test-secret",
    )