from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    launching = "launching"
    running = "running"
    exited = "exited"
    failed = "failed"


class JobStatus(str, Enum):
    pending = "pending"
    launching = "launching"
    running = "running"
    summarizing = "summarizing"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class AgentInfo(BaseModel):
    id: str
    display_name: str
    command: str
    installed: bool
    description: str


class CreateSessionRequest(BaseModel):
    agent_id: str = Field(description="Agent adapter id")
    cwd: str = Field(default=".", description="Working directory")
    prompt: Optional[str] = Field(default=None, description="Initial prompt")
    parent_session_id: Optional[str] = None
    root_session_id: Optional[str] = None


class SessionSummary(BaseModel):
    session_id: str
    agent_id: str
    status: SessionStatus
    cwd: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    parent_session_id: Optional[str] = None
    root_session_id: Optional[str] = None
    depth: int


class SubTaskRequest(BaseModel):
    title: str
    agent_id: str
    prompt: str
    cwd: str = "."


class SpawnSubSessionsRequest(BaseModel):
    owner_session_id: str
    strategy: str = Field(default="parallel", pattern="^(parallel|serial)$")
    max_concurrency: int = Field(default=2, ge=1, le=8)
    timeout_s: int = Field(default=1800, ge=30, le=7200)
    tasks: list[SubTaskRequest]


class SubTaskResult(BaseModel):
    task_id: str
    title: str
    session_id: Optional[str] = None
    status: JobStatus = JobStatus.pending
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None
    error: Optional[str] = None


class OrchestrationJobView(BaseModel):
    job_id: str
    owner_session_id: str
    strategy: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    timeout_s: int
    max_concurrency: int
    tasks: list[SubTaskResult]
