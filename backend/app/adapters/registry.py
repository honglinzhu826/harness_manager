from __future__ import annotations

from app.adapters.base import AgentAdapter


def build_registry() -> dict[str, AgentAdapter]:
    adapters = [
        AgentAdapter(
            id="codex",
            display_name="Codex CLI",
            command="codex",
            description="OpenAI Codex CLI interactive TUI",
        ),
        AgentAdapter(
            id="claude",
            display_name="Claude Code",
            command="claude",
            description="Anthropic Claude Code interactive TUI",
        ),
        AgentAdapter(
            id="kimi",
            display_name="Kimi CLI",
            command="kimi",
            description="Moonshot Kimi interactive TUI",
        ),
    ]
    return {adapter.id: adapter for adapter in adapters}
