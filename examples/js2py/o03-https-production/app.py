"""Local diagnostics ONLY: no real authentication, authorization, tasks or DB."""
import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

logger = logging.getLogger("js2py.safe")
LOCAL_ORIGIN = "https://frontend.lab.test:8444"


class ProbeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minutes: StrictInt = Field(ge=0)


def create_app():
    app = FastAPI(debug=False, docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def safe_errors(request: Request, call_next):
        request_id = uuid4().hex  # Do not trust an unbounded caller-provided log id.
        try:
            response = await call_next(request)
        except Exception:
            # Teaching event only: never include body, query, token, exception or traceback.
            logger.warning("unhandled_error request_id=%s", request_id)
            response = JSONResponse({"detail": "Internal server error"}, status_code=500)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        details = [{"loc": list(error["loc"]), "type": error["type"]}
                   for error in exc.errors()]
        return JSONResponse({"detail": details}, status_code=422)

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/probe")
    def probe(request: Request):
        return {"scheme": request.url.scheme, "host": request.url.hostname,
                "client": request.client.host,
                "authorization_present": "authorization" in request.headers}

    @app.post("/probe")
    def input_probe(body: ProbeInput):
        return {"minutes": body.minutes}

    @app.get("/fail")
    def fail():
        raise RuntimeError("FICTIONAL_INTERNAL_DETAIL_DO_NOT_RETURN")

    # Global CORS wraps even sanitized error responses. Host validation still applies
    # to actual endpoint requests. This fixed local origin is not a production default.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["lab.test", "127.0.0.1"])
    return CORSMiddleware(app, allow_origins=[LOCAL_ORIGIN], allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        expose_headers=["X-Request-ID", "Idempotency-Replayed"])
