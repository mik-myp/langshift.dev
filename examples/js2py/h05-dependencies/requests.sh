#!/bin/sh
# Run against a fresh local server. No API-test framework is required.
set -eu
base=http://127.0.0.1:8005
curl -i "$base/health"
curl -i -X POST "$base/tasks" -H 'Content-Type: application/json' \
  -d '{"title":"  Read Python  ","minutes":30,"note":"keep"}'
curl -i "$base/tasks?limit=1&offset=0"
curl -i -X PATCH "$base/tasks/1" -H 'Content-Type: application/json' -d '{}'
curl -i -X PATCH "$base/tasks/1" -H 'Content-Type: application/json' -d '{"note":null}'
curl -i -X POST "$base/tasks" -H 'Content-Type: application/json' -d '{"title":"Bad","minutes":true}'
curl -i "$base/tasks/99999"
