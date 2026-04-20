# Harness Manager

Harness Manager is an open-source GUI control plane for running multiple **code agent TUIs** through persistent PTY sessions.

## Core Idea

- Harness Manager does **not** reimplement agent protocols.
- It launches each agent as a real TUI process (`codex`, `claude`, `kimi`) with `ptyprocess`.
- The GUI lets users manage sessions, send input, and stream outputs.
- A built-in orchestrator allows one session to spawn sub-sessions for sub-task workflows.

## Repository Layout

- `backend/`: FastAPI service, agent adapters, PTY session manager, sub-session orchestrator.
- `frontend/`: React + xterm.js launcher/workspace UI.
- `docs/`: architecture and skill contract documents.

## Backend Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend Quick Start

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE` if backend is not on `http://localhost:8000/api`.

## MVP API Surface

- `GET /api/agents`
- `POST /api/sessions`
- `GET /api/sessions`
- `POST /api/sessions/{id}/input`
- `GET /api/sessions/{id}/drain`
- `DELETE /api/sessions/{id}`
- `POST /api/orchestrator/jobs`
- `GET /api/orchestrator/jobs/{job_id}`
- `POST /api/orchestrator/jobs/{job_id}/cancel`
