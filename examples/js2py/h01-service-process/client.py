"""A one-request CLIENT, not a listening server. Only 127.0.0.1."""
from http.client import HTTPConnection, HTTPException
import sys


def fetch(port: int, path: str) -> tuple[int, str]:
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("use a local request path such as /hello.txt")
    connection = HTTPConnection("127.0.0.1", port, timeout=3)
    try:
        connection.request("GET", path, headers={"Connection": "close"})
        response = connection.getresponse()
        return response.status, response.read().decode("utf-8")
    finally:
        connection.close()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python client.py PORT /PATH", file=sys.stderr)
        return 2
    try:
        status, body = fetch(int(sys.argv[1]), sys.argv[2])
    except (OSError, HTTPException, ValueError) as error:
        print(f"client error: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(f"status={status}")
    print(body, end="" if body.endswith("\n") else "\n")
    return 0 if status < 400 else 2


if __name__ == "__main__":
    raise SystemExit(main())
