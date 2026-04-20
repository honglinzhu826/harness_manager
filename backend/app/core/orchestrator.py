from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic

from app.adapters.base import AgentAdapter
from app.core.session_manager import SessionManager
from app.models.schemas import (
    JobStatus,
    OrchestrationJobView,
    SpawnSubSessionsRequest,
    SubTaskResult,
)


@dataclass
class JobRuntime:
    view: OrchestrationJobView
    cancel_event: threading.Event = field(default_factory=threading.Event)


class SubSessionOrchestrator:
    def __init__(self, session_manager: SessionManager):
        self._session_manager = session_manager
        self._jobs: dict[str, JobRuntime] = {}
        self._lock = threading.Lock()

    def spawn(
        self,
        request: SpawnSubSessionsRequest,
        adapters: dict[str, AgentAdapter],
    ) -> OrchestrationJobView:
        now = datetime.now(timezone.utc)
        job_id = str(uuid.uuid4())
        tasks = [
            SubTaskResult(task_id=str(uuid.uuid4()), title=t.title)
            for t in request.tasks
        ]
        view = OrchestrationJobView(
            job_id=job_id,
            owner_session_id=request.owner_session_id,
            strategy=request.strategy,
            status=JobStatus.pending,
            created_at=now,
            updated_at=now,
            timeout_s=request.timeout_s,
            max_concurrency=request.max_concurrency,
            tasks=tasks,
        )
        runtime = JobRuntime(view=view)

        with self._lock:
            self._jobs[job_id] = runtime

        worker = threading.Thread(
            target=self._run_job,
            args=(runtime, request, adapters),
            daemon=True,
        )
        worker.start()
        return view

    def _run_job(
        self,
        runtime: JobRuntime,
        request: SpawnSubSessionsRequest,
        adapters: dict[str, AgentAdapter],
    ) -> None:
        runtime.view.status = JobStatus.launching
        runtime.view.updated_at = datetime.now(timezone.utc)

        if request.strategy == "serial":
            self._run_serial(runtime, request, adapters)
        else:
            self._run_parallel(runtime, request, adapters)

    def _run_serial(
        self,
        runtime: JobRuntime,
        request: SpawnSubSessionsRequest,
        adapters: dict[str, AgentAdapter],
    ) -> None:
        runtime.view.status = JobStatus.running
        for idx, task in enumerate(request.tasks):
            if runtime.cancel_event.is_set():
                runtime.view.status = JobStatus.cancelled
                return
            result = runtime.view.tasks[idx]
            self._launch_task(runtime, result, task.agent_id, task.cwd, task.prompt, adapters)
            if result.status == JobStatus.failed:
                runtime.view.status = JobStatus.failed
                runtime.view.updated_at = datetime.now(timezone.utc)
                return
        runtime.view.status = JobStatus.succeeded
        runtime.view.updated_at = datetime.now(timezone.utc)

    def _run_parallel(
        self,
        runtime: JobRuntime,
        request: SpawnSubSessionsRequest,
        adapters: dict[str, AgentAdapter],
    ) -> None:
        runtime.view.status = JobStatus.running
        sem = threading.Semaphore(request.max_concurrency)
        threads: list[threading.Thread] = []

        def runner(idx: int) -> None:
            task = request.tasks[idx]
            result = runtime.view.tasks[idx]
            with sem:
                if runtime.cancel_event.is_set():
                    result.status = JobStatus.cancelled
                    return
                self._launch_task(runtime, result, task.agent_id, task.cwd, task.prompt, adapters)

        for i in range(len(request.tasks)):
            t = threading.Thread(target=runner, args=(i,), daemon=True)
            threads.append(t)
            t.start()

        deadline = monotonic() + request.timeout_s
        for t in threads:
            remaining = max(0.0, deadline - monotonic())
            t.join(timeout=remaining)

        statuses = {task.status for task in runtime.view.tasks}
        if any(t.is_alive() for t in threads):
            runtime.cancel_event.set()
            runtime.view.status = JobStatus.failed
            for task in runtime.view.tasks:
                if task.status in {JobStatus.pending, JobStatus.running, JobStatus.launching}:
                    task.status = JobStatus.failed
                    task.error = "Task timed out before completion"
                    task.ended_at = datetime.now(timezone.utc)
        elif JobStatus.failed in statuses:
            runtime.view.status = JobStatus.failed
        elif JobStatus.cancelled in statuses:
            runtime.view.status = JobStatus.cancelled
        elif JobStatus.pending in statuses or JobStatus.running in statuses or JobStatus.launching in statuses:
            runtime.view.status = JobStatus.failed
        else:
            runtime.view.status = JobStatus.succeeded
        runtime.view.updated_at = datetime.now(timezone.utc)

    def _launch_task(
        self,
        runtime: JobRuntime,
        result: SubTaskResult,
        agent_id: str,
        cwd: str,
        prompt: str,
        adapters: dict[str, AgentAdapter],
    ) -> None:
        adapter = adapters.get(agent_id)
        result.started_at = datetime.now(timezone.utc)
        if not adapter:
            result.status = JobStatus.failed
            result.error = f"Unknown adapter: {agent_id}"
            result.ended_at = datetime.now(timezone.utc)
            return
        try:
            session = self._session_manager.create_session(
                adapter=adapter,
                cwd=cwd,
                prompt=prompt,
                model=None,
                parent_session_id=runtime.view.owner_session_id,
                root_session_id=runtime.view.owner_session_id,
            )
            result.session_id = session.session_id
            result.status = JobStatus.succeeded
            result.summary = f"Spawned sub session {session.session_id} via {agent_id}"
        except Exception as exc:  # noqa: BLE001
            result.status = JobStatus.failed
            result.error = str(exc)
        finally:
            result.ended_at = datetime.now(timezone.utc)
            runtime.view.updated_at = datetime.now(timezone.utc)

    def get_job(self, job_id: str) -> OrchestrationJobView:
        runtime = self._jobs.get(job_id)
        if not runtime:
            raise KeyError(job_id)
        return runtime.view

    def cancel(self, job_id: str) -> OrchestrationJobView:
        runtime = self._jobs.get(job_id)
        if not runtime:
            raise KeyError(job_id)
        runtime.cancel_event.set()
        runtime.view.status = JobStatus.cancelled
        runtime.view.updated_at = datetime.now(timezone.utc)
        return runtime.view
