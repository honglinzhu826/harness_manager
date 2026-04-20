from __future__ import annotations

import shutil
from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentAdapter:
    id: str
    display_name: str
    command: str
    description: str
    default_args: list[str] = field(default_factory=list)
    model_arg: str | None = None
    supported_models: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)

    def is_installed(self) -> bool:
        return shutil.which(self.command) is not None

    def launch_argv(self, model: str | None = None) -> list[str]:
        argv = [self.command, *self.default_args]
        if model and self.model_arg:
            argv.extend([self.model_arg, model])
        return argv
