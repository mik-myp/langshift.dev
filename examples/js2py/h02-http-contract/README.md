# H02: HTTP contracts aligned with H04–H06

Version `h02-task-contract-v2-h04-aligned`. Checked 2026-09-28. **This lab still contains contract samples, pure previews, and static serving only, not task CRUD.**

## Separate the core from optional hardening

Prerequisites are H01 processes, requests, ports, and trust boundaries. The core uses `/tasks` and `id/title/minutes/done/note`: preserve title spelling/surrounding spaces but reject entirely blank text; minutes is a required strict nonnegative integer; done is a strict boolean defaulting false; note is nullable and defaults null; the service generates id. PATCH preserves omissions, clears explicit note=null, and applies 0/false. Empty PATCH is a valid no-op.

Pagination defaults limit to 20 with a maximum of 100 and offset to 0 with a nonnegative constraint. Sort by id; return `items/limit/offset/total`, without next_offset or status filters. 404 uses text detail; 422 uses an array, including malformed JSON. title/minutes/done are not nullable, unknown body keys are rejected, and internal_tag is excluded from output.

See `CONTRACT.md` (Chinese `CONTRACT.zh-cn.md`, traditional Chinese `CONTRACT.zh-tw.md`) for the complete agreement. Projects, members, identity, and database relationships are future D/S evolution, not current fields. HEAD, unknown-query rejection, 413/415, custom errors, Location, and production redaction are not claimed H04 guarantees. Actual gaps are in `gaps/h04-observations.json`.

## File semantics

The 24 files in `public/exchanges` are independent. `kind` labels a proposal; `precondition.seed_tasks` states its starting conditions; `request`/`response` describe an exchange rather than an additional online wrapper. Object request.body values are JSON-encoded. The malformed-json string is raw proposed text, not another layer of JSON quoting. A null response.body for 204 means no transmitted body, not four transmitted characters null.

Downloading a creation sample with real HTTP 200 is not executing creation with 201. Reading a deletion sample deletes no task. wire files are readable excerpts omitting Date/length details, not captures or HTTP encoders. check_example verifies selected invariants and preview_page uses parsed Python values; neither replaces H04 validation or HTTP parsing.

## Environment and reproduction

Pin CPython 3.13.15 and pytest 8.4.2, requires-python `>=3.13,<3.14`, package=false. Tested uv 0.12.13, macOS, curl 8.7.1. H02 does not install FastAPI. The maintainer separately checked an isolated H04 copy using FastAPI 0.135.1 / Uvicorn 0.42.0 / Pydantic 2.12.5. Shared H04 source and lockfiles were not modified.

Repository users enter the lab from the repository root; download users enter extracted h02-http-contract and start with uv sync.

```bash
cd examples/js2py/h02-http-contract
pwd
uv sync --locked --default-index https://pypi.org/simple
uv run --locked python --version
uv run --locked python contract_examples.py
uv run --locked python inspect_transport.py
uv run --locked python -m pytest -q
uv run --locked python -m pytest -q solutions/test_review_cases.py
```

The final contract-check line:

```text
checked 24 proposed exchanges; no CRUD requests executed
```

Standard suite: 47 checks (43 sample/calculation, 4 real HTTP). Independent suite: 5 checks. Actual transport output:

```text
real GET example: HTTP 200; proposed POST: 201
real GET tasks: HTTP 404
real POST tasks: HTTP 501; no CRUD implemented
real HEAD example: HTTP 200; body bytes=0
real GET with Origin: HTTP 200; allow-origin=False
service_alive=True
owned_service_stopped=True
```

HEAD here belongs to the standard-library static tool, not H04 task routes; H04 HEAD /tasks returned 405. Do not automatically transfer one tool's behavior to another application's guarantees.

## Actual requests in two terminals

A and B both use the lab root. Start in foreground A:

```bash
uv run --locked python -m http.server 8767 --bind 127.0.0.1 --directory public
```

`-m` runs the standard-library module ; 8767 is the listening port; `--bind` restricts loopback; `--directory public` is relative to A's startup directory. Not returning a prompt while awaiting requests is normal.

In B:

```bash
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8767/exchanges/create-ok.json'
curl --noproxy '*' --max-time 3 --include 'http://127.0.0.1:8767/tasks'
curl --noproxy '*' --max-time 3 --include --header 'Content-Type: application/json' --data-binary @requests/create.json 'http://127.0.0.1:8767/tasks'
curl --noproxy '*' --max-time 3 --include --fail-with-body 'http://127.0.0.1:8767/tasks'
echo $?
```

Statuses are 200/404/501/404; the last curl exits 22. curl is a client. `--noproxy '*'` bypasses proxies with quotes preventing shell expansion; `--max-time 3` bounds the transfer; `--include` displays headers/body; `--header` adds a header; `--data-binary @...` reads B's file as-is and defaults to POST; `--fail-with-body` retains HTTP error content and produces nonzero exit. Default curl may exit 0 on HTTP errors; command exit status is not HTTP status.

```bash
curl --noproxy '*' --max-time 3 --include --header 'Origin: https://untrusted.invalid' 'http://127.0.0.1:8767/exchanges/create-ok.json'
curl --noproxy '*' --max-time 3 --include --request OPTIONS --header 'Origin: http://127.0.0.1:5173' --header 'Access-Control-Request-Method: POST' --header 'Access-Control-Request-Headers: content-type' 'http://127.0.0.1:8767/tasks'
```

These return 200 without Allow-Origin, then 501. `--request OPTIONS` selects the method; header domains are not connection destinations and are not visited. curl does not enforce browser response sharing, so it cannot prove browser CORS success. CORS is not authentication, authorization, or complete CSRF protection.

Press Ctrl+C in A to stop only your foreground instance. Automation uses another allocated loopback port and cleans only its own child, not manual A. Identify your own listener or change ports on collisions; never kill unidentified listeners by port. Serve only public, without .env, project/home directories, symbolic links, or real data.

## Intentional failure and independent work

```bash
uv run --locked python -m pytest -q errors/test_wrong_contract.py
```

Expect 1 assertion failure and exit 1: the wrong assertion expects 200 instead of 204. Correct the assertion and bodyless client branch, not the valid sample. The error file is outside default tests. This is an assertion failure, not HTTP 500.

First write four normal exchanges: second page (limit 1 / offset 1), beyond-end empty page, PATCH omitting note, and explicit null. Add 422 cases for minutes=null and limit 101. Explain why empty PATCH is unchanged but 0/false are real assignments. solutions contains five pure calculation/consistency tests and six complete exchanges, not online CRUD tests.

## Resume and verified boundaries

Record v2, edited samples, directory, owned service terminal/port, last commands, 47+5 results, and the next step. Stop the service. Resume with offline checks and inspect_transport, then manual requests. Do not infer persistence of earlier tasks.

This snapshot verifies H02 samples, pagination, independent work, deliberate failure, and static transport. The maintainer also checked 24 core exchanges and 5 gaps against an isolated H04 copy. HEAD 405, ignored unknown queries, media errors 422 rather than 415, and valid JSON above 64 KiB still returning 201 are gap observations, not extra core promises. Source hashes accompany the gap record.

Unimplemented/unverified: H02 CRUD, full schemas, login/permissions, database, concurrent idempotency, enforced body limits, production redaction, real browser CORS, TLS, public deployment, Linux/Windows execution, final ZIPs, and whole-site integration. The matching external -files.json explicitly lists publishing files, excluding environments, caches, logs, and credentials.

## Primary sources

Checked 2026-09-28: [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), [RFC 5789](https://www.rfc-editor.org/rfc/rfc5789.html), [Pydantic strict mode](https://github.com/pydantic/pydantic/blob/v2.12.5/docs/concepts/strict_mode.md), [response models](https://fastapi.tiangolo.com/tutorial/response-model/), [partial updates](https://fastapi.tiangolo.com/tutorial/body-updates/), [error handling](https://fastapi.tiangolo.com/tutorial/handling-errors/), [Fetch/CORS](https://fetch.spec.whatwg.org/#http-cors-protocol), [http.server](https://docs.python.org/3.13/library/http.server.html), [http.client](https://docs.python.org/3.13/library/http.client.html), [curl](https://curl.se/docs/manpage.html).
