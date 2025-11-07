from __future__ import annotations

from dataclasses import dataclass

from src.quant.agents.runners import OpenAITradeAgent
from src.quant.core.types import PromptPayload


@dataclass
class _DummyMessage:
	content: str


@dataclass
class _DummyChoice:
	message: _DummyMessage

	@classmethod
	def from_content(cls, content: str) -> _DummyChoice:
		return cls(message=_DummyMessage(content))


class _DummyCompletion:
	def __init__(self, choice: _DummyChoice) -> None:
		self.choices = [choice]
		self.usage = {"prompt_tokens": 10, "completion_tokens": 20}

	def model_dump(self) -> dict[str, object]:
		return {
			"choices": [
				{"message": {"content": self.choices[0].message.content}},
			],
			"usage": self.usage,
		}


class _DummyChatCompletions:
	def __init__(self, content: str) -> None:
		self._content = content

	def create(self, **_: object) -> _DummyCompletion:
		return _DummyCompletion(_DummyChoice.from_content(self._content))


class _DummyChat:
	def __init__(self, content: str) -> None:
		self.completions = _DummyChatCompletions(content)


class _DummyClient:
	def __init__(self, content: str) -> None:
		self.chat = _DummyChat(content)


def test_openai_trade_agent_generates_response() -> None:
	client = _DummyClient('[{"symbol":"AAPL.US","action":"buy","quantity":5}]')
	agent = OpenAITradeAgent(client=client, model="dummy")
	prompt = PromptPayload(content="Trade AAPL", metadata={"system": "sys", "user": "usr"})
	response = agent.generate(prompt)
	assert response.raw_text
	assert response.signals and response.signals[0].symbol == "AAPL.US"
	assert response.metadata["usage"]["prompt_tokens"] == 10
