"""Agent orchestration helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

from src.quant.core.interfaces import AgentRunner
from src.quant.core.types import AgentResponse, PromptPayload

if TYPE_CHECKING:
	from src.quant.execution.logger import ExecutionLogger


class AgentCoordinator:
	"""Runs multiple AgentRunner implementations and collects their responses."""

	def __init__(
		self,
		runners: Iterable[AgentRunner] | None = None,
		*,
		logger: ExecutionLogger | None = None,
	) -> None:
		self._runners: list[AgentRunner] = list(runners or [])
		self._logger = logger

	def register(self, runner: AgentRunner) -> None:
		"""Register an additional agent runner."""
		self._runners.append(runner)

	def gather(self, prompt: PromptPayload) -> Sequence[AgentResponse]:
		"""Execute the prompt against each registered runner."""
		if self._logger:
			self._logger.log_prompt(prompt)
		responses: list[AgentResponse] = []
		for runner in self._runners:
			response = runner.generate(prompt)
			if self._logger:
				self._logger.log_agent_response(response)
			responses.append(response)
		return responses
