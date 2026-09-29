"""Loopback-only teaching client; never print or put a bearer/password in argv."""
import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import stat
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a bearer to a redirect target.


def redact(value):
    secret_names = {"access_token", "password", "password_hash", "token_digest", "authorization", "current_password", "new_password"}
    if isinstance(value, dict):
        return {key: "<redacted>" if key.lower() in secret_names else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def request(port, method, path, body=None, token=None, key=None):
    if not path.startswith("/") or path.startswith("//"):
        raise ValueError("Use a local absolute API path")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if key:
        headers["Idempotency-Key"] = key
    data = json.dumps(body).encode() if body is not None else None
    req = Request(f"http://127.0.0.1:{port}" + path, data=data, method=method, headers=headers)
    try:
        # A loopback URL alone is NOT isolation: urllib inherits proxy settings.
        response = build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=10)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else None, dict(response.headers)


def save_token(path: Path, token: str):
    # Refuse symlinks; create a private replacement, then atomically rename it.
    if path.is_symlink():
        raise ValueError("Refusing session-file symlink")
    temporary = path.with_name(path.name + ".new")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump({"access_token": token}, stream)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_token(path: Path):
    if path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("Session file must be private mode 0600, not a symlink")
    return json.loads(path.read_text())["access_token"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8061)
    parser.add_argument("--session", type=Path, default=Path(".session-alice.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("login").add_argument("login")
    commands.add_parser("change-password")
    send = commands.add_parser("request")
    send.add_argument("method", choices=["GET", "POST", "PATCH", "DELETE"])
    send.add_argument("path")
    send.add_argument("--json", default=None, help="Non-secret business JSON only")
    send.add_argument("--key", default=None)
    args = parser.parse_args()
    if args.command == "login":
        status, body, headers = request(args.port, "POST", "/auth/token",
                               {"login": args.login, "password": getpass("Password: ")})
        if status == 200:
            save_token(args.session, body["access_token"])
            print("HTTP 200; bearer saved in private session file; expires_in", body["expires_in"])
        else:
            print("HTTP", status, "login rejected; no credential printed")
        return
    token = read_token(args.session)
    if args.command == "change-password":
        body = {"current_password": getpass("Current password: "),
                "new_password": getpass("New password (15..128 characters): ")}
        if body["new_password"] != getpass("Confirm new password: "):
            raise ValueError("Passwords do not match")
        status, result, headers = request(args.port, "POST", "/users/me/password", body, token)
        print("HTTP", status, "password-change result; no credential printed")
        if status == 204:
            args.session.unlink()
        return
    if args.path.split("?")[0] in ("/auth/token", "/users/me/password"):
        raise ValueError("Use the dedicated secret-prompt command, not --json")
    body = json.loads(args.json) if args.json else None
    status, result, headers = request(args.port, args.method, args.path, body, token, args.key)
    print("HTTP", status)
    if "idempotency-replayed" in headers:
        print("Idempotency-Replayed:", headers["idempotency-replayed"])
    print(json.dumps(redact(result), ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError):
        # No traceback/exception repr that might expose a session file or URL header.
        raise SystemExit("Client operation failed; check local service, private session file and inputs") from None
