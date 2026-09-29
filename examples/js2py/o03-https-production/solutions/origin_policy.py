"""Independent requirement: exactly two approved browser origins, no cookies."""
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI

ORIGINS = ["https://frontend.lab.test:8444", "https://admin.lab.test:8445"]


def create_app():
    app = FastAPI()
    @app.post("/probe")
    def probe():
        return {"authenticated": False}  # This exercise implements no authentication.
    return CORSMiddleware(app, allow_origins=ORIGINS, allow_credentials=False,
        allow_methods=["POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        expose_headers=["Idempotency-Replayed"])
