"""Factory helpers for constructing DeepSeek OpenAI-compatible clients."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from src.core.config import settings


@dataclass(slots=True)
class DeepSeekClientConfig:
	"""Runtime configuration for DeepSeek API access."""

	api_key: str
	base_url: str | None = None
	model: str = "deepseek-chat"
	timeout: float | None = None
	default_headers: dict[str, str] = field(default_factory=dict)

	@classmethod
	def from_settings(cls) -> DeepSeekClientConfig:
		return cls(
			api_key=settings.DEEPSEEK_API_KEY,
			base_url=settings.DEEPSEEK_BASE_URL,
			model=settings.DEEPSEEK_MODEL,
			timeout=settings.DEEPSEEK_TIMEOUT,
		)


def create_deepseek_client(
	config: DeepSeekClientConfig | None = None,
	**overrides: Any,
) -> OpenAI:
	"""Instantiate the OpenAI-compatible client for DeepSeek."""

	config = config or DeepSeekClientConfig.from_settings()
	api_key = overrides.get("api_key", config.api_key)
	base_url = overrides.get("base_url", config.base_url)
	headers = {**config.default_headers, **overrides.get("default_headers", {})}
	client_kwargs: dict[str, Any] = {}
	if base_url:
		client_kwargs["base_url"] = base_url
	if headers:
		client_kwargs["default_headers"] = headers
	if config.timeout is not None:
		client_kwargs["timeout"] = config.timeout
	for key, value in overrides.items():
		if key in {"api_key", "base_url", "default_headers"}:
			continue
		client_kwargs[key] = value
	return OpenAI(api_key=api_key, **client_kwargs)


__all__ = ["DeepSeekClientConfig", "create_deepseek_client"]
