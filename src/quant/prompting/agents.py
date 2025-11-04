"""Agent orchestration helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from quant.core.interfaces import AgentRunner
from quant.core.types import AgentResponse, PromptPayload


class AgentCoordinator:
    """Runs multiple AgentRunner implementations and collects their responses."""

    def __init__(self, runners: Iterable[AgentRunner] | None = None) -> None:
        self._runners: list[AgentRunner] = list(runners or [])

    def register(self, runner: AgentRunner) -> None:
        """Register an additional agent runner."""
        self._runners.append(runner)

    def gather(self, prompt: PromptPayload) -> Sequence[AgentResponse]:
        """Execute the prompt against each registered runner."""
        return [runner.generate(prompt) for runner in self._runners]
