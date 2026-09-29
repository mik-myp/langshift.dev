"""Observe real HTTP separately from the proposed status inside a JSON file."""
import json
from pathlib import Path
from tools.owned_server import exchange, owned_server

ROOT = Path(__file__).resolve().parent


def inspect() -> list[str]:
    with owned_server(ROOT / "public") as (process, port):
        status, _, body = exchange(port, "/exchanges/create-ok.json")
        example = json.loads(body)
        lines = [f"real GET example: HTTP {status}; proposed POST: {example['response']['status']}"]
        status, _, _ = exchange(port, "/tasks")
        lines.append(f"real GET tasks: HTTP {status}")
        status, _, _ = exchange(port, "/tasks", "POST",
                                b'{"title":"Ship the draft","minutes":15}',
                                {"Content-Type": "application/json"})
        lines.append(f"real POST tasks: HTTP {status}; no CRUD implemented")
        status, headers, body = exchange(port, "/exchanges/create-ok.json", "HEAD")
        lines.append(f"real HEAD example: HTTP {status}; body bytes={len(body)}")
        status, headers, _ = exchange(port, "/exchanges/create-ok.json",
                                      headers={"Origin": "https://untrusted.invalid"})
        allowed = any(name.lower() == "access-control-allow-origin" for name in headers)
        lines.append(f"real GET with Origin: HTTP {status}; allow-origin={allowed}")
        lines.append(f"service_alive={process.poll() is None}")
    lines.append(f"owned_service_stopped={process.poll() is not None}")
    return lines


if __name__ == "__main__":
    print("\n".join(inspect()))
