"""Owned local processes/sockets/temp keys. No DNS change, system CA install or -k."""
import argparse
from contextlib import contextmanager
import http.client
import json
import os
from pathlib import Path
import shutil
import shlex
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
import time

from certificates import create_certificates
from edge import create_edge

ROOT = Path(__file__).resolve().parent


@contextmanager
def backend(directory: Path, trust_proxy=True):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0)); listener.listen()
    port = listener.getsockname()[1]
    args = [sys.executable, "-m", "uvicorn", "app:create_app", "--factory",
            "--fd", str(listener.fileno()), "--no-access-log", "--log-level", "warning"]
    args += ["--proxy-headers", "--forwarded-allow-ips", "127.0.0.1"] if trust_proxy else ["--no-proxy-headers"]
    with (directory / "backend.log").open("w") as output:
        process = subprocess.Popen(args, cwd=ROOT, pass_fds=(listener.fileno(),),
                                   stdout=output, stderr=subprocess.STDOUT)
        listener.close()
        try:
            deadline = time.monotonic() + 8
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("owned backend failed; inspect its private backend.log")
                try:
                    if direct(port, "/health/live")[0] == 200:
                        yield port
                        break
                except OSError:
                    pass
                time.sleep(.03)
            else:
                raise TimeoutError("owned backend not ready")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)


def direct(port, path="/probe", headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
    try:
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()


@contextmanager
def running(port=0):
    # /tmp explicitly: neither lab source nor home directory receives private keys.
    with TemporaryDirectory(prefix="js2py-tls-", dir="/tmp") as temp:
        directory = Path(temp)
        ca = create_certificates(directory)
        with backend(directory) as backend_port:
            server = create_edge(backend_port, directory, port)
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": .05}, daemon=True)
            thread.start()
            try:
                yield {"port": server.server_port, "backend_port": backend_port, "ca": ca, "directory": directory}
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)
                if thread.is_alive():
                    raise RuntimeError("owned TLS thread did not stop")


def curl(lab, path="/probe", *, trusted=True, hostname="lab.test", extra=()):
    binary = shutil.which("curl")
    if not binary:
        raise RuntimeError("curl required")
    args = [binary, "--silent", "--show-error", "--noproxy", "*", "--max-time", "5",
            "--resolve", f"{hostname}:{lab['port']}:127.0.0.1"]
    if trusted:
        args += ["--cacert", str(lab["ca"])]
    args += list(extra) + ["--write-out", "\n%{http_code}", f"https://{hostname}:{lab['port']}{path}"]
    return subprocess.run(args, capture_output=True, text=True, timeout=8)


def decoded(result):
    if result.returncode:
        raise RuntimeError(f"curl transport failed: exit {result.returncode}")
    body, status = result.stdout.rsplit("\n", 1)
    return int(status), json.loads(body)


def observe():
    with running() as lab:
        status, body = decoded(curl(lab, extra=("-H", "Authorization: Bearer demo-not-a-valid-session",
            "-H", "X-Forwarded-For: 203.0.113.9", "-H", "X-Forwarded-Proto: http")))
        assert status == 200 and body["scheme"] == "https" and body["client"] == "127.0.0.1"
        assert body["authorization_present"] is True
        untrusted = curl(lab, trusted=False)
        hostname = curl(lab, hostname="wrong.test")
        assert untrusted.returncode == hostname.returncode == 60
        failure_status, failure = decoded(curl(lab, "/fail"))
        assert failure_status == 500 and failure == {"detail": "Internal server error"}
        bad_status, bad = decoded(curl(lab, extra=("-H", "Content-Type: application/json", "--data", '{"minutes":"fictional-sensitive-input"}')))
        assert bad_status == 422 and "fictional-sensitive-input" not in json.dumps(bad)
        oversize, _ = decoded(curl(lab, extra=("--data-binary", "x" * 4097)))
        assert oversize == 413
        # This demonstrates the residual trust boundary, NOT a safe user identity.
        _, local_spoof = direct(lab["backend_port"], headers={"X-Forwarded-For": "203.0.113.9", "X-Forwarded-Proto": "https"})
        assert local_spoof["client"] == "203.0.113.9"
        log = (lab["directory"] / "backend.log").read_text()
        assert "demo-not-a-valid-session" not in log and "FICTIONAL_INTERNAL" not in log
        location = lab["directory"]
        with backend(lab["directory"], trust_proxy=False) as untrusted_backend:
            _, ignored = direct(untrusted_backend, headers={"X-Forwarded-Proto": "https", "X-Forwarded-For": "203.0.113.9"})
            assert ignored["scheme"] == "http" and ignored["client"] == "127.0.0.1"
    assert not location.exists()
    return ["trusted_ca_https=200", "unknown_ca_curl_exit=60", "wrong_hostname_curl_exit=60",
            "edge_overwrites_forged_forwarding=True", "authorization_forwarded_not_authenticated=True",
            "untrusted_proxy_headers_ignored=True", "trusted_loopback_direct_spoof_possible=True",
            "sanitized_error=500", "sanitized_validation=422", "teaching_edge_body_limit=413",
            "owned_processes_stopped_and_temp_keys_removed=True"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8443)
    args = parser.parse_args()
    if not args.serve:
        print("\n".join(observe())); return
    with running(args.port) as lab:
        print(f"URL=https://lab.test:{lab['port']}/probe", flush=True)
        print(f"PUBLIC_CA={lab['ca']}", flush=True)
        print(f"export CA={shlex.quote(str(lab['ca']))}", flush=True)
        print(f"export PORT={lab['port']}", flush=True)
        print("Loopback teaching service only. Ctrl+C stops owned processes and removes temporary keys.", flush=True)
        try:
            while True:
                time.sleep(.2)
        except KeyboardInterrupt:
            print("stopping owned teaching service", flush=True)


if __name__ == "__main__":
    main()
