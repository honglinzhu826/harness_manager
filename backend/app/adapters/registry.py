from __future__ import annotations

from app.adapters.base import AgentAdapter


def build_registry() -> dict[str, AgentAdapter]:
    adapters = [
        AgentAdapter(
            id="codex",
            display_name="Codex CLI",
            command="codex",
            description="OpenAI Codex CLI interactive TUI",
            model_arg="--model",
            supported_models=["gpt-5", "gpt-5-mini", "gpt-4.1"],
        ),
        AgentAdapter(
            id="claude",
            display_name="Claude Code",
            command="claude",
            description="Anthropic Claude Code interactive TUI",
            model_arg="--model",
            supported_models=["claude-opus-4", "claude-sonnet-4", "claude-3.7-sonnet"],
        ),
        AgentAdapter(
            id="kimi",
            display_name="Kimi CLI",
            command="kimi",
            description="Moonshot Kimi interactive TUI",
            model_arg="--model",
            supported_models=["kimi-k2", "kimi-thinking", "kimi-latest"],
        ),
    ]
    return {adapter.id: adapter for adapter in adapters}
