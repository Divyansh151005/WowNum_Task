from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import feedback
from .routers.feedback import create_tables


def create_app() -> FastAPI:
    app = FastAPI(title="WowNom Feedback Collector", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(feedback.router, prefix="/api/feedback", tags=["feedback"])

    @app.get("/healthz")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Ensure DB tables exist when the app is created (covers TestClient too)
    create_tables()

    return app


app = create_app()


