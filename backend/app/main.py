from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.registry import build_registry
from app.api.routes import build_router
from app.core.orchestrator import SubSessionOrchestrator
from app.core.session_manager import SessionManager


@dataclass
class AppState:
    adapters: dict
    session_manager: SessionManager
    orchestrator: SubSessionOrchestrator


def create_app() -> FastAPI:
    adapters = build_registry()
    session_manager = SessionManager(max_depth=3)
    orchestrator = SubSessionOrchestrator(session_manager=session_manager)
    state = AppState(
        adapters=adapters,
        session_manager=session_manager,
        orchestrator=orchestrator,
    )

    app = FastAPI(title="Harness Manager API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_router(state), prefix="/api")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
