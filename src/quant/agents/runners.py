"""AgentRunner implementations using OpenAI-compatible APIs."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from openai import OpenAI

from quant.core.interfaces import AgentRunner
from quant.core.types import AgentResponse, PromptPayload

from .client import DeepSeekClientConfig, create_deepseek_client
from .parsers import parse_trade_suggestions


class OpenAITradeAgent(AgentRunner):
	"""Execute prompts using an OpenAI-compatible chat completion API."""

	def __init__(
		self,
		client: OpenAI,
		*,
		model: str,
		temperature: float = 0.2,
		max_tokens: int | None = 1024,
	) -> None:
		self._client = client
		self._model = model
		self._temperature = temperature
		self._max_tokens = max_tokens

	def generate(self, prompt: PromptPayload) -> AgentResponse:
		"""Execute the provided prompt and capture the Agent response."""
		messages = _build_messages(prompt)
		try:
			completion = self._client.chat.completions.create(
				model=self._model,
				messages=messages,
				temperature=self._temperature,
				max_tokens=self._max_tokens,
			)
		except Exception as exc:  # pragma: no cover - network/runtime errors
			return AgentResponse(raw_text="", metadata={"error": str(exc)})

		choice = completion.choices[0] if completion.choices else None
		response_text = choice.message.content if choice and choice.message else ""
		signals = list(parse_trade_suggestions(response_text))
		metadata = {
			"raw_response": _safe_dump(completion),
			"usage": _safe_dump(getattr(completion, "usage", None)),
		}
		return AgentResponse(raw_text=response_text or "", signals=signals, metadata=metadata)


def create_default_agent_runner(
	config: DeepSeekClientConfig | None = None,
) -> OpenAITradeAgent:
	"""Factory returning an ``OpenAITradeAgent`` preconfigured for DeepSeek."""
	config = config or DeepSeekClientConfig.from_settings()
	client = create_deepseek_client(config)
	return OpenAITradeAgent(client, model=config.model)


def _build_messages(prompt: PromptPayload) -> Sequence[dict[str, Any]]:
	metadata = prompt.metadata or {}
	if "messages" in metadata:
		return metadata["messages"]
	messages: list[dict[str, Any]] = []
	system_prompt = metadata.get("system")
	if system_prompt:
		messages.append({"role": "system", "content": system_prompt})
	user_prompt = metadata.get("user") or prompt.content
	if user_prompt:
		messages.append({"role": "user", "content": user_prompt})
	return messages


def _safe_dump(obj: Any) -> Any:
	if obj is None:
		return None
	if isinstance(obj, (dict, list, str, int, float, type(None))):
		return obj
	if hasattr(obj, "model_dump"):
		return obj.model_dump()
	if hasattr(obj, "dict"):
		return obj.dict()
	return str(obj)


__all__ = ["OpenAITradeAgent", "create_default_agent_runner"]
