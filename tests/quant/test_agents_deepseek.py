from __future__ import annotations

from dataclasses import dataclass

from quant.agents import DeepSeekClientConfig
from quant.agents.runners import OpenAITradeAgent, create_default_agent_runner
from quant.core.types import PromptPayload


@dataclass
class _FakeMessage:
	content: str


@dataclass
class _FakeChoice:
	message: _FakeMessage


class _FakeCompletion:
	def __init__(self, content: str) -> None:
		self.choices = [_FakeChoice(_FakeMessage(content))]
		self.usage = {"prompt_tokens": 42, "completion_tokens": 21}

	def model_dump(self) -> dict[str, object]:
		return {
			"choices": [
				{"message": {"content": self.choices[0].message.content}},
			],
			"usage": self.usage,
		}


def test_deepseek_runner_invokes_client(monkeypatch) -> None:
	config = DeepSeekClientConfig(api_key="test", base_url="https://mock", model="deepseek-chat")
	runner = create_default_agent_runner(config)
	assert isinstance(runner, OpenAITradeAgent)

	captured: dict[str, object] = {}

	def fake_create(*_, **kwargs):
		captured.update(kwargs)
		return _FakeCompletion('[{"symbol":"AAPL.US","action":"buy","quantity":3}]')

	monkeypatch.setattr(runner._client.chat.completions, "create", fake_create, raising=True)  # type: ignore[attr-defined]

	payload = PromptPayload(
		content="Generate trade",
		metadata={"system": "You are trader", "user": "你是谁"},
	)
	response = runner.generate(payload)
	print(response)

	# assert response.signals and response.signals[0].symbol == "AAPL.US"
	# assert captured["model"] == config.model
	# assert captured["messages"][0]["role"] == "system"
