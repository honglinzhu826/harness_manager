from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import (
    AgentInfo,
    CreateSessionRequest,
    OrchestrationJobView,
    SessionSummary,
    SpawnSubSessionsRequest,
)


class InputRequest(BaseModel):
    data: str


class DrainResponse(BaseModel):
    chunks: list[str]


def build_router(state) -> APIRouter:
    router = APIRouter()

    @router.get("/agents", response_model=list[AgentInfo])
    def list_agents() -> list[AgentInfo]:
        return [
            AgentInfo(
                id=adapter.id,
                display_name=adapter.display_name,
                command=adapter.command,
                installed=adapter.is_installed(),
                description=adapter.description,
                supported_models=adapter.supported_models,
            )
            for adapter in state.adapters.values()
        ]

    @router.post("/sessions", response_model=SessionSummary)
    def create_session(req: CreateSessionRequest) -> SessionSummary:
        adapter = state.adapters.get(req.agent_id)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {req.agent_id}")
        try:
            return state.session_manager.create_session(
                adapter=adapter,
                cwd=req.cwd,
                prompt=req.prompt,
                model=req.model,
                parent_session_id=req.parent_session_id,
                root_session_id=req.root_session_id,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (FileNotFoundError, NotADirectoryError, OSError) as exc:
            raise HTTPException(status_code=400, detail=f"Failed to spawn PTY session: {exc}") from exc

    @router.get("/sessions", response_model=list[SessionSummary])
    def list_sessions() -> list[SessionSummary]:
        return state.session_manager.list_sessions()

    @router.get("/sessions/{session_id}", response_model=SessionSummary)
    def get_session(session_id: str) -> SessionSummary:
        try:
            return state.session_manager.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc

    @router.post("/sessions/{session_id}/input")
    def write_session(session_id: str, req: InputRequest) -> dict[str, str]:
        try:
            state.session_manager.write(session_id, req.data)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        return {"status": "ok"}

    @router.get("/sessions/{session_id}/drain", response_model=DrainResponse)
    def drain_session(session_id: str) -> DrainResponse:
        try:
            chunks = state.session_manager.read_since_last(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Session not found") from exc
        return DrainResponse(chunks=chunks)

    @router.delete("/sessions/{session_id}")
    def terminate_session(session_id: str) -> dict[str, str]:
        state.session_manager.terminate(session_id)
        return {"status": "terminated"}

    @router.post("/orchestrator/jobs", response_model=OrchestrationJobView)
    def spawn_sub_sessions(req: SpawnSubSessionsRequest) -> OrchestrationJobView:
        return state.orchestrator.spawn(req, state.adapters)

    @router.get("/orchestrator/jobs/{job_id}", response_model=OrchestrationJobView)
    def get_job(job_id: str) -> OrchestrationJobView:
        try:
            return state.orchestrator.get_job(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    @router.post("/orchestrator/jobs/{job_id}/cancel", response_model=OrchestrationJobView)
    def cancel_job(job_id: str) -> OrchestrationJobView:
        try:
            return state.orchestrator.cancel(job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc

    return router
