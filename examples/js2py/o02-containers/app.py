"""Health-only deployment smoke app. NO accounts, tasks, or authorization."""
import os
from tempfile import TemporaryFile

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import data_directory


def create_app() -> FastAPI:
    directory = data_directory(os.environ)
    app = FastAPI(title="O02 health-only smoke app", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health/live")
    def live():
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready():
        try:
            with TemporaryFile(dir=directory) as probe:
                probe.write(b"local-write-probe")
                probe.flush()
        except OSError:
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        return {"status": "ready"}

    return app
