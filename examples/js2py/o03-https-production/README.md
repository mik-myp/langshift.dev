# O03 HTTPS, reverse proxies, and production boundaries

Prerequisite: O02. Diagnostics run only on127.0.0.1, implement no real identity/task database, and must not be public. S uses opaque Authorization Bearer sessions with DB digest+expiry/revoked+auth_version, not JWT or auth cookies. This tool proves only fictional-header forwarding, never authentication.

## Environment and restoration

Checked **2026-09-28**. Use an ordinary POSIX account, not root, for permission experiments. CPython **3.13.15**, uv **0.12.13**, pytest **8.4.2**. `.python-version` selects the interpreter, pyproject declares `>=3.13,<3.14`, and uv.lock fixes resolution. `[tool.uv] package=false` means the lab is not built as a distributable Python package.

Web baseline: FastAPI **0.135.1**, Uvicorn **0.42.0**, Pydantic **2.12.5**, HTTPX **0.28.1**, Starlette **0.52.1**, AnyIO **4.12.1**. No frontend dependencies.

Repository users run the cd below from the repository root. ZIP users enter the extracted lab root directly, where pyproject.toml resides. `--locked` refuses silent lock changes.

```bash
cd examples/js2py/o03-https-production
pwd
uv --version
uv sync --locked
uv run --locked python --version
```

The maintainer actually generated the lock using `uv lock --default-index https://pypi.org/simple`. Restoration does not require fresh resolution. Environments/caches are excluded from the allowlist/ZIP; data experiments use owned temporary directories.

Additional tools: OpenSSL3.x with req -addext/-noenc (tested3.6.4), curl (tested8.7.1). No system software is installed automatically. certificates.py creates a one-day temporary CA and lab.test leaf only in an owned /tmp directory, with0700 directory/0600 files. It neither installs system trust nor packages/prints keys.

```bash
openssl version
curl --version
uv run --locked python tls_lab.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_origin_policy.py
uv run --locked python check_config.py
```

```text
trusted_ca_https=200
unknown_ca_curl_exit=60
wrong_hostname_curl_exit=60
edge_overwrites_forged_forwarding=True
authorization_forwarded_not_authenticated=True
untrusted_proxy_headers_ignored=True
trusted_loopback_direct_spoof_possible=True
sanitized_error=500
sanitized_validation=422
teaching_edge_body_limit=413
owned_processes_stopped_and_temp_keys_removed=True
```

## Two-terminal interaction and stopping

Run the first command in terminalA. --serve stays in the foreground and --port 0 requests an available port. Copy the actual printed export CA and export PORT lines into terminalB. CA points to public trust material, not a private key. Remain at the lab root when invoking curl. --resolve overrides this client’s DNS mapping while retaining SNI/Host; --cacert verifies using the selected CA; --noproxy avoids external proxies; --max-time bounds waiting; --include displays response headers; -H supplies a request header.

```bash
uv run --locked python tls_lab.py --serve --port 0
```

```bash
curl --silent --show-error --include --max-time 5 --noproxy '*' --resolve "lab.test:$PORT:127.0.0.1" --cacert "$CA" -H 'Authorization: Bearer demo-not-a-valid-session' "https://lab.test:$PORT/probe"
```

Expect200, scheme=https and authorization_present=true, without authentication. Omitting --cacert or changing both URL/resolve to wrong.test produces curl exit60. Never count -k as verification. Ctrl+C in terminalA stops owned backend/edge and removes temporary keys. The old CA path then becomes invalid; copy fresh values on the next launch. Automatic mode also cleans up without killall.

## Mechanisms and deliberate gaps

edge.py is a bounded standard-library teaching forwarder, not a production HTTP parser. It forwards an explicit header set and overwrites forwarding metadata. Its4096-byte413 policy is local, not an H04/S03 promise. app.py returns safe500 and loc/type-only422 without input/traceback echoes; logs contain only safe events and random IDs. /fail is local fault injection.

Disabled proxy trust ignores forged headers; the edge overwrites them; but other local processes can connect directly to trusted127.0.0.1 upstream and spoof values. This is an observed residual risk requiring real deployment isolation, not allow-ips=* to repair URLs. TLS does not look up sessions, authorize members, or revoke tokens.

Exact-origin CORS permits demonstration GET/POST and Authorization/Content-Type/Idempotency-Key; the full S API needs its actual method policy. allow_credentials=False and no cookies. CORS is not authentication and curl does not enforce browser response restrictions. A cookie migration requires fresh CSRF/SameSite/Secure/HttpOnly/origin/anti-CSRF assessment. Real browsers remain unverified.

## Caddy/public deployment (unexecuted)

Caddyfile.local uses a same-host loopback8034 upstream and explicit TLS_CERT/TLS_KEY paths. production.template retains api.example.invalid and cannot be deployed directly. Caddy is absent, so only check_config text invariants ran; no caddy validate/runtime evidence exists. On your own controlled host with a fixed Caddy version, independent certificates and target app, the command below can run the local diagnostic upstream for configuration testing—not production. Prepare certificate paths before validating local configuration; never borrow real user private keys.

```bash
uv run --locked python -m uvicorn app:create_app --factory --host 127.0.0.1 --port 8034 --proxy-headers --forwarded-allow-ips 127.0.0.1 --no-access-log
caddy validate --config Caddyfile.local --adapter caddyfile
```

The first command runs in the foreground; run the second in another terminal after preparing certificate environment variables. Stop the first with Ctrl+C. Separate containers cannot communicate through each other’s loopback; topology changes require renewed upstream/trust review. Public DNS, public issuance/renewal, access boundaries, full S03 revocation/auth/DB readiness, request bounds and login throttling, release/rollback and backup/restore all remain pending. No public resources are created.

## Independent requirement

Permit exactly the HTTPS frontend.lab.test:8444 and admin.lab.test:8445 origins. Reject wrong ports, HTTP, malicious hostname suffixes and null preflights. Use no cookies; do not call direct no-Origin access authentication. Write your solution/tests before reading solutions/origin_policy.py and its7 independent cases.

## Environment matrix (machine-readable: ENVIRONMENT.json)

| State | Evidence / gate |
| --- | --- |
| actually_run | OpenSSL3.6.4 temporary CA/leaf and restrictive key modes; real local TLS with curl8.7.1 --cacert; no -k; unknown CA and wrong hostname each curl60; proxy disabled ignores spoofed headers; edge overwrites spoofed headers; direct trusted-loopback spoof remains possible and is explicitly demonstrated; fictional Authorization forwarding WITHOUT authentication; generic500, safe422/no input echo, safe event log; local teaching-edge413 only; CORS preflight and actual-response headers; exact-origin independent tests; owned backend/edge shutdown and temporary-key removal; selected Caddy text invariants only |
| unavailable_here | Caddy binary; controlled Linux/container environment; user domain/host/production secrets not provided |
| user_must_supply | controlled host and fixed reviewed production reverse-proxy version; owned domain and DNS administration; approved firewall/challenge ports and certificate persistence; production configuration/secret storage; never teaching keys; real browser/frontend and full S03 authorized backend |
| pending_acceptance | caddy validate/adapt and actual Caddy runtime; real DNS A/AAAA and external reachability; trusted public certificate issuance/renewal; non-bypassable upstream isolation and multi-proxy trust if applicable; actual browser integration and CSRF reassessment on any cookie migration; full S03 session/revocation/authorization/DB readiness and header integration; production body bounds/login throttling/password-hash capacity; migration/release/rollback/backup/restore; no real-user launch |

This run passed **17 standard** and **7 independent** cases. Source/text are `implemented`; external environment gates remain `environment_pending`, not deployment acceptance. Ordinary macOS tests do not replace Linux/container/public or Windows evidence.

## Resume and diagnosis record

Record source/lock hashes, cwd, tool versions, last successful command, failure stage/category, actual case counts, environment matrix, and next first step. Never record a full environment, real token, database URL, or private key. Resume with `uv sync --locked`, standard tests, and your own independent tests. A passing reference alone does not establish independent ability.

## Primary sources

SOURCES.json records official URLs, scope, HTTP retrieval results and SHA-256 digests checked on 2026-09-28. The chapter explains mechanisms; this README provides the offline execution entry. No production resource creation, system-software installation, or acceptance of service terms is automated here.
