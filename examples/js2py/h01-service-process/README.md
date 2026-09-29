# H01: From client to a long-running service

Status: a local lab, not a task API or deployable backend. Checked 2026-09-28.

## Goal and scope

Prerequisites are L10 local projects and L14 resource lifetimes. Start a process, observe loopback listening, trace a request to a file, distinguish request completion from process termination, diagnose 404/connection failure/port collision, and stop only your own service. HTTP server implementation, FastAPI, databases, authentication, and async are not required.

Expose only `public` or the reference `solutions/public`. Do not expose the project root, home directory, credentials, `.env`, or symbolic links. `http.server` follows symbolic links and may list directories; it is not a security sandbox. Loopback is not authentication.

## Environment and working directory

Pin CPython 3.13.15 in `.python-version`, with range `>=3.13,<3.14`; pytest 8.4.2 is a development dependency. Tested with uv 0.12.13, macOS, and curl 8.7.1. No third-party runtime dependencies. Commands use a macOS/Linux shell; Windows terminal and signal behavior are not verified.

Repository users enter the directory below from the repository root. Download users enter the extracted `h01-service-process` and start at `uv sync`.

```bash
cd examples/js2py/h01-service-process
pwd
uv sync --locked --default-index https://pypi.org/simple
uv run --locked python --version
uv run --locked python one_shot.py
uv run --locked python observe.py
uv run --locked python -m pytest -q
uv run --locked python -m solutions.observe_health
uv run --locked python -m pytest -q solutions/test_health.py
```

Stable `observe.py` output:

```text
200 hello from the service
404 missing
200 hello from the service
request_done_process_alive=True
process_stopped=True
```

The standard 13 tests and 2 independent-reference tests pass. The independent reference returns `ready` for health and succeeds again after 404. Automation listens only on `127.0.0.1`, lets the OS allocate a port, and cleans up its own child in finally. Tests establish the listed local behavior, not production concurrency, external-network security, or persistence.

## Two terminals and real requests

Both A and B use the lab root. Start the foreground service in A:

```bash
uv run --locked python -m http.server 8765 --bind 127.0.0.1 --directory public
```

`-m` runs the standard-library module; `8765` selects the port; `--bind` limits listening to loopback; `--directory` selects the public directory relative to A's startup directory. The missing prompt is normal while the service waits.

Send requests from B:

```bash
curl --noproxy '*' --max-time 3 --verbose 'http://127.0.0.1:8765/hello.txt'
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8765/not-here.txt'
echo $?
uv run --locked python client.py 8765 /hello.txt
```

curl is a client, not a listener. `--noproxy '*'` bypasses proxies; quotes prevent shell expansion. `--max-time 3` bounds the whole transfer. `--verbose` sends connection/header diagnostics to standard error; `--include` displays response headers with the body. First observe 200 and `hello from the service`, then 404 with an HTML error page. curl can exit zero after an HTTP error by default. `echo $?` is a command exit status, not HTTP status. The Python client exits zero on success, 2 on an HTTP error, and 1 on connection exceptions.

Return to A and press Ctrl+C to stop only that foreground instance. A repeat request from B exits 7 without an HTTP response in the tested condition where nobody takes over the port. Restore using the original start command. Do not use `killall`, kill unknown processes by port, expose `0.0.0.0`, or add a public tunnel.

## Diagnosis and exercises

- `Address already in use` means startup failed to acquire a listener. Identify your prior instance; if uncertain, choose `8766` and update all clients. Do not stop an unknown process.
- 404 is an HTTP response: check path and public directory rather than reinstalling Python. Changing the public directory to `solutions/public` makes `/hello.txt` return 404 and `/health.txt` return 200.
- Connection failure precedes an HTTP response. Check your process, host, and port. Reproduce by stopping your own service, not probing others.
- Independent task: use another directory and port for health success, missing-path failure, and note success; prove the old hello file is not shared. Attempt it before reading `solutions`.

Explanation answer: a client exits only itself; the service keeps its listening resource. A 404 proves neither resource existence nor, by itself, the identity of the intended responding process. A disabled frontend input cannot constrain other clients; later the server must validate and authorize.

## Pause/resume and file roles

Record the working/public directories, port, owning terminal, last successful/failed commands, failure layer, 13+2 test results, and first next step. Stop your instance before pausing. Resume with `observe.py`, then repeat manual success/failure/success. Do not kill a PID merely because it appears in old notes.

`client.py` is a one-request client; `observe.py` observes lifetimes; `tools/owned_server.py` is bounded test infrastructure, not required student server implementation. It uses only the standard-library CLI and never scans ports to stop other programs. `tests` is the standard suite; `solutions` contains independent references. The external matching `-files.json` explicitly allowlists download contents, excluding `.venv`, caches, temporary logs, and credentials.

## Primary sources

Checked 2026-09-28: [http.server](https://docs.python.org/3.13/library/http.server.html), [http.client](https://docs.python.org/3.13/library/http.client.html), [subprocess](https://docs.python.org/3.13/library/subprocess.html), [curl](https://curl.se/docs/manpage.html), [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), [IANA loopback](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry.xhtml), and [WHATWG URL](https://url.spec.whatwg.org/). Public networking, TLS, browser cross-origin policy, databases, and production deployment are unverified.
