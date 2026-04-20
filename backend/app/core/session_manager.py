from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Optional

from ptyprocess import PtyProcess

from app.adapters.base import AgentAdapter
from app.models.schemas import SessionStatus, SessionSummary


@dataclass
class SessionRuntime:
    summary: SessionSummary
    pty: PtyProcess
    output_buffer: list[str] = field(default_factory=list)
    queue: Queue[str] = field(default_factory=Queue)
    stop_event: threading.Event = field(default_factory=threading.Event)


class SessionManager:
    def __init__(self, max_depth: int = 3):
        self._sessions: dict[str, SessionRuntime] = {}
        self._lock = threading.Lock()
        self._max_depth = max_depth

    def create_session(
        self,
        adapter: AgentAdapter,
        cwd: str,
        prompt: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        root_session_id: Optional[str] = None,
    ) -> SessionSummary:
        depth = 0
        if parent_session_id:
            parent = self._sessions.get(parent_session_id)
            if not parent:
                raise ValueError(f"Parent session not found: {parent_session_id}")
            depth = parent.summary.depth + 1
        if depth > self._max_depth:
            raise ValueError(f"Session depth {depth} exceeded max depth {self._max_depth}")

        started_at = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())
        summary = SessionSummary(
            session_id=session_id,
            agent_id=adapter.id,
            status=SessionStatus.launching,
            cwd=cwd,
            started_at=started_at,
            parent_session_id=parent_session_id,
            root_session_id=root_session_id or parent_session_id or session_id,
            depth=depth,
        )
        env = {**os.environ, **adapter.env}
        pty = PtyProcess.spawn(adapter.launch_argv(), cwd=cwd, env=env)

        runtime = SessionRuntime(summary=summary, pty=pty)

        with self._lock:
            self._sessions[session_id] = runtime
            runtime.summary.status = SessionStatus.running

        if prompt:
            self.write(session_id, prompt + "\n")

        threading.Thread(target=self._read_loop, args=(session_id,), daemon=True).start()
        return runtime.summary

    def _read_loop(self, session_id: str) -> None:
        runtime = self._sessions[session_id]
        pty = runtime.pty
        while not runtime.stop_event.is_set():
            try:
                chunk = pty.read(2048)
                if not chunk:
                    break
                text = chunk.decode(errors="ignore")
                runtime.output_buffer.append(text)
                runtime.queue.put(text)
            except EOFError:
                break
            except OSError:
                break

        runtime.summary.ended_at = datetime.now(timezone.utc)
        runtime.summary.status = SessionStatus.exited if pty.exitstatus == 0 else SessionStatus.failed

    def list_sessions(self) -> list[SessionSummary]:
        with self._lock:
            return [runtime.summary for runtime in self._sessions.values()]

    def get_session(self, session_id: str) -> SessionSummary:
        runtime = self._sessions.get(session_id)
        if not runtime:
            raise KeyError(session_id)
        return runtime.summary

    def write(self, session_id: str, data: str) -> None:
        runtime = self._sessions.get(session_id)
        if not runtime:
            raise KeyError(session_id)
        runtime.pty.write(data.encode())

    def read_since_last(self, session_id: str, max_chunks: int = 100) -> list[str]:
        runtime = self._sessions.get(session_id)
        if not runtime:
            raise KeyError(session_id)
        chunks: list[str] = []
        for _ in range(max_chunks):
            try:
                chunks.append(runtime.queue.get_nowait())
            except Empty:
                break
        return chunks

    def terminate(self, session_id: str) -> None:
        runtime = self._sessions.get(session_id)
        if not runtime:
            return
        runtime.stop_event.set()
        try:
            runtime.pty.terminate(force=True)
        finally:
            runtime.summary.ended_at = datetime.now(timezone.utc)
            runtime.summary.status = SessionStatus.exited
