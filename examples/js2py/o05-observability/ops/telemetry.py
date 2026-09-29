import json
import math
import os
import time
import uuid

from fastapi.responses import JSONResponse
from ops.app import create_app as base_app


def create_app():
    app=base_app()
    destination=app.state.root/"events.jsonl"

    @app.middleware("http")
    async def observe(request,call_next):
        # Never reflect an untrusted header into logs: it may contain a secret.
        request_id=uuid.uuid4().hex
        started=time.perf_counter()
        error_type=None
        try:
            response=await call_next(request)
        except Exception:
            error_type="unhandled_error"
            response=JSONResponse(status_code=500,content={"detail":"Internal Server Error"})
        route=request.scope.get("route")
        # Whitelist fields: NEVER serialize request, URL query, headers, body or exception.
        event={"event":"http_request","request_id":request_id,"timestamp":time.time(),
               "method":request.method if request.method in {"GET","POST","PATCH","DELETE","OPTIONS"} else "OTHER",
               "route":getattr(route,"path","unmatched"),"status":response.status_code,
               "ready_ms":round((time.perf_counter()-started)*1000,3),
               "error_type":error_type or ("server_error" if response.status_code>=500 else None)}
        fd=os.open(destination,os.O_WRONLY|os.O_APPEND|os.O_CREAT,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as output:output.write(json.dumps(event,sort_keys=True)+"\n")
        response.headers["X-Request-ID"]=request_id
        return response
    return app


def summarize(events):
    # A finite lab observation window, not a distributed metrics backend.
    if not events:return {"requests":0,"server_errors":0,"error_rate":0.0,"p95_ready_ms":0.0,"alert":"insufficient_data"}
    durations=sorted(event["ready_ms"] for event in events)
    errors=sum(event["status"]>=500 for event in events)
    rate=errors/len(events)
    return {"requests":len(events),"server_errors":errors,"error_rate":round(rate,4),
            "p95_ready_ms":durations[math.ceil(.95*len(durations))-1],
            "alert":"insufficient_data" if len(events)<20 else ("page" if rate>=.05 else "ok")}
