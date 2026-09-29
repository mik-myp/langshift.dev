"""Probe readiness inside this container; no proxy or secret output."""
import json
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener


def main() -> int:
    try:
        with build_opener(ProxyHandler({})).open("http://127.0.0.1:8000/health/ready", timeout=2) as response:
            return 0 if response.status == 200 and json.load(response) == {"status": "ready"} else 1
    except (OSError, URLError, ValueError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
