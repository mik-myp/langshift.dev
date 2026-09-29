from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from task_api.config import Settings, load_settings
from task_api.routes import router
from task_api.store import MemoryStore


def create_app(settings: Settings | None = None) -> FastAPI:
    # Called once per application, before Uvicorn starts accepting requests.
    settings = load_settings() if settings is None else settings
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.store = MemoryStore()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5506"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
