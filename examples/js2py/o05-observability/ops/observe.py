import json
import secrets
import time
from ops.cluster import OwnedCluster,connect
from ops.data import grant_app,seed
from ops.migrate import upgrade
from ops.server import running
from ops.telemetry import summarize


def drill():
    with OwnedCluster() as cluster:
        root=cluster.root
        upgrade(root,"007_project_description");grant_app(root);tokens=seed(root)
        canary="synthetic-private-"+secrets.token_hex(16)
        headers={"Authorization":"Bearer "+tokens["alice"],"Cookie":"session="+canary,"X-Request-ID":tokens["alice"]}
        started=time.perf_counter()
        with running(root,"v2",factory="ops.telemetry:create_app") as client:
            for _ in range(20):assert client.get("/projects/1",headers=headers).status_code==200
            bad=client.post("/projects",headers=headers,json={"name":"Safe","password":canary})
            assert bad.status_code==422 and canary not in bad.text
            assert client.get("/projects/1?token="+canary,headers=headers).status_code==200
            assert client.get("/projects/1",headers={"Authorization":"Bearer invalid","X-Request-ID":canary+"!"}).status_code==401
            with connect(root,"source") as conn:conn.execute("REVOKE SELECT ON projects FROM lab_app")
            fault_ids=[]
            for _ in range(5):
                response=client.get("/projects/1",headers=headers)
                assert response.status_code==503
                fault_ids.append(response.headers["X-Request-ID"])
            events=[json.loads(line) for line in (root/"events.jsonl").read_text().splitlines()]
            fault=[event for event in events if event["request_id"] in fault_ids]
            assert len(fault)==5 and all(event["status"]==503 and event["route"]=="/projects/{project_id}" for event in fault)
            assert summarize(events)["alert"]=="page"
            print("PASS correlate: real HTTP 503 -> request_id -> route template -> revoked DB privilege")
            with connect(root,"source") as conn:conn.execute("GRANT SELECT ON projects TO lab_app")
            headers["X-Request-ID"]="read-after-repair"
            for _ in range(20):assert client.get("/projects/1",headers=headers).status_code==200
        events=[json.loads(line) for line in (root/"events.jsonl").read_text().splitlines()]
        assert summarize(events[-20:])["alert"]=="ok"
        for event in events:
            assert set(event)=={"event","request_id","timestamp","method","route","status","ready_ms","error_type"}
            assert event["ready_ms"]>=0
            assert "?" not in event["route"]
        for path in root.glob("*.log"):
            text=path.read_text()
            assert canary not in text and all(token not in text for token in tokens.values())
        text=(root/"events.jsonl").read_text()
        assert canary not in text and all(token not in text for token in tokens.values())
        print("PASS privacy: synthetic password/cookie/query/Bearer canaries absent from event, service and PostgreSQL logs")
        print("OBSERVATION",json.dumps({**summarize(events),"elapsed_seconds":round(time.perf_counter()-started,3),"scope":"one local worker, sequential synthetic traffic; NOT production capacity"},sort_keys=True))
        print("PASS repair: final 20 real requests healthy; alert cleared")
    assert not root.exists()
    print("CLEANUP PASS: private logs and owned services removed")
