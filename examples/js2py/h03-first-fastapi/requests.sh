#!/usr/bin/env bash
# Start app:app on 127.0.0.1:8003 in another terminal first.
# This is a visible request worksheet, not an assertion suite.
curl -sS -i http://127.0.0.1:8003/health
curl -sS -i http://127.0.0.1:8003/tasks/1
curl -sS -i 'http://127.0.0.1:8003/tasks?limit=1&offset=1'
curl -sS -i 'http://127.0.0.1:8003/tasks?offset=99'
curl -sS -i http://127.0.0.1:8003/tasks/999
curl -sS -i http://127.0.0.1:8003/tasks/nope
curl -sS -i http://127.0.0.1:8003/tasks/0
curl -sS -i 'http://127.0.0.1:8003/tasks?limit=0'
curl -sS -i 'http://127.0.0.1:8003/tasks?offset=-1'
curl -sS -i http://127.0.0.1:8003/missing
curl -sS -i -X POST http://127.0.0.1:8003/tasks
