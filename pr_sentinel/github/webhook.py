import hashlib
import hmac


def verify_github_signature(
    payload_body: bytes,
    signature_header: str | None,
    secret: str | None,
) -> bool:
    if not secret:
        return True

    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    received_signature = signature_header.removeprefix("sha256=")

    return hmac.compare_digest(expected_signature, received_signature)