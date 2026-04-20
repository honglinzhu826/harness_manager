# PTY Orchestrator Skill Contract

This document defines the skill-facing contract for sub-session orchestration.

## Goals

- Let a root TUI agent launch child TUI sessions for delegated tasks.
- Keep child sessions isolated and traceable.
- Return structured results to parent session.

## Actions

### 1) Spawn job

`POST /api/orchestrator/jobs`

Request body (`SpawnSubSessionsRequest`):

- `owner_session_id`
- `strategy`: `parallel` or `serial`
- `max_concurrency`
- `timeout_s`
- `tasks[]`: `title`, `agent_id`, `prompt`, `cwd`

### 2) Poll job

`GET /api/orchestrator/jobs/{job_id}`

### 3) Cancel job

`POST /api/orchestrator/jobs/{job_id}/cancel`

## State Model

### Job states

`pending -> launching -> running -> (succeeded|failed|cancelled)`

### Task states

`pending -> (succeeded|failed|cancelled)`

## Session Lineage

Each child session is created with:

- `parent_session_id = owner_session_id`
- `root_session_id = owner_session_id`

Depth is validated by `SessionManager(max_depth=3)`.

## MVP Notes

- Successful task completion currently means the PTY child session was created and prompt injected.
- Final work-product validation and summaries are deferred to next iteration.
