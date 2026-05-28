import base64
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/encode_github_app_key.py /path/to/private-key.pem")
        raise SystemExit(1)

    key_path = Path(sys.argv[1]).expanduser()

    if not key_path.exists():
        print(f"Private key file not found: {key_path}")
        raise SystemExit(1)

    encoded = base64.b64encode(key_path.read_bytes()).decode("utf-8")
    print(encoded)


if __name__ == "__main__":
    main()