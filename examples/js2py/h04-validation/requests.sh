#!/usr/bin/env bash
# Start a FRESH app:app on 127.0.0.1:8004 in another terminal first.
# This worksheet mutates only the disposable teaching service. Read every response.
# 01: empty collection, 200
curl -sS -i http://127.0.0.1:8004/tasks
# 02: create, 201; surrounding spaces must survive
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"  Read HTTP  ","minutes":25,"note":"keep me"}'
# 03: default done=false and note=null, 201
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Zero","minutes":0}'
# 04: stable page, only id=2; total=2
curl -sS -i 'http://127.0.0.1:8004/tasks?limit=1&offset=1'
# 05: only done changes; title, minutes, note survive
curl -sS -i -X PATCH http://127.0.0.1:8004/tasks/1 -H 'Content-Type: application/json' --data-binary '{"done":true}'
# 06: empty patch is a 200 no-op
curl -sS -i -X PATCH http://127.0.0.1:8004/tasks/1 -H 'Content-Type: application/json' --data-binary '{}'
# 07: explicit false and zero must not be dropped
curl -sS -i -X PATCH http://127.0.0.1:8004/tasks/1 -H 'Content-Type: application/json' --data-binary '{"done":false,"minutes":0}'
# 08: a new string replaces note
curl -sS -i -X PATCH http://127.0.0.1:8004/tasks/1 -H 'Content-Type: application/json' --data-binary '{"note":"new"}'
# 09: explicit null clears note
curl -sS -i -X PATCH http://127.0.0.1:8004/tasks/1 -H 'Content-Type: application/json' --data-binary '{"note":null}'
# 10-17: invalid bodies, all 422, no new records
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":" ","minutes":1}'
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Bad","minutes":true}'
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Bad","minutes":"25"}'
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Bad","minutes":25.0}'
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Bad","minutes":-1}'
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Bad","minutes":1,"done":"false"}'
curl -sS -i -X PATCH http://127.0.0.1:8004/tasks/1 -H 'Content-Type: application/json' --data-binary '{"title":null}'
curl -sS -i -X POST http://127.0.0.1:8004/tasks -H 'Content-Type: application/json' --data-binary '{"title":"Bad","minutes":1,"user_id":7}'
# 18-20: path/query errors versus valid-but-missing id
curl -sS -i 'http://127.0.0.1:8004/tasks?limit=101'
curl -sS -i http://127.0.0.1:8004/tasks/nope
curl -sS -i http://127.0.0.1:8004/tasks/999
# 21: persisted in this process, no internal_tag in response
curl -sS -i http://127.0.0.1:8004/tasks/1
# 22: delete, 204 and ZERO body bytes
curl -sS -i -X DELETE http://127.0.0.1:8004/tasks/1
# 23-24: now missing, 404
curl -sS -i http://127.0.0.1:8004/tasks/1
curl -sS -i -X DELETE http://127.0.0.1:8004/tasks/1
# 25: id=2 remains; stop and restart, then run this request again: items=[]
curl -sS -i http://127.0.0.1:8004/tasks
