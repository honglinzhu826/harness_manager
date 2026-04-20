# Harness Manager: Design Requirements & Architecture (v0.1)

## Product Requirements Summary

1. The project is an open-source Harness Manager GUI application that controls multiple code-agent CLIs.
2. The product is explicitly TUI-first: Codex CLI, Claude Code, and Kimi CLI are launched as native TUI sessions.
3. Python backend owns session lifecycle and orchestration.
4. PTY layer is implemented with `ptyprocess`, and sessions are persistent by default.
5. GUI uses React frontend + Python backend.
6. A skill-like orchestration API must support spawning sub sessions for sub-task planning.

## Architecture Decisions

- **No protocol rewriting** for agent behavior. Harness simply hosts native TUI processes.
- **Per-tab PTY process model**: each user session maps to one `ptyprocess.PtyProcess`.
- **Hierarchy-aware sessions** to support parent/child relationships and bounded recursion depth.
- **Orchestrator API** supports `parallel` and `serial` sub-task execution strategies.
- **Adapter registry** keeps launch details per agent while preserving a unified interface.

## Backend Components

- `adapters/`: metadata and launch command registry for codex/claude/kimi.
- `core/session_manager.py`: PTY process lifecycle, streaming buffer, input routing, depth limits.
- `core/orchestrator.py`: sub-session job creation, concurrency, cancellation, and job status views.
- `api/routes.py`: REST interfaces for agents, sessions, and orchestration jobs.

## Frontend Components

- Launcher sidebar for agent/cwd selection.
- Workspace terminal view using `xterm.js`.
- Session state store with Zustand.
- Poll-based streaming API integration for MVP.

## Security & Stability Guardrails

- Maximum sub-session depth (default 3).
- Maximum orchestration concurrency (validated per request).
- Explicit termination endpoint for process cleanup.
- Designed to avoid logging secrets from CLI environment.

## Next Iteration Suggestions

- Upgrade polling to WebSocket bidirectional streaming.
- Add durable session metadata storage (SQLite/PostgreSQL).
- Add artifact collection and structured summaries per sub-task.
- Add role-based controls for multi-user deployments.
