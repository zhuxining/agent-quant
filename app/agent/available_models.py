from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from agno.models.deepseek import DeepSeek
from agno.models.openai.like import OpenAILike

from app.core.config import settings

ModelName = Literal["kimi", "deepseek"]
if settings.ENVIRONMENT == "dev":
	CACHE_RESPONSES = True


def _build_kimi() -> OpenAILike:
	return OpenAILike(
		id=settings.KIMI_MODEL,
		name="Kimi",
		api_key=settings.KIMI_API_KEY,
		base_url="https://api.moonshot.cn/v1",
		cache_response=CACHE_RESPONSES,
	)


def _build_deepseek() -> DeepSeek:
	return DeepSeek(
		id=settings.DEEPSEEK_MODEL,
		cache_response=CACHE_RESPONSES,
	)


MODEL_BUILDERS: dict[ModelName, Callable[[], OpenAILike]] = {
	"kimi": _build_kimi,
	"deepseek": _build_deepseek,
}


def get_available_model(name: ModelName) -> OpenAILike:
	if name not in MODEL_BUILDERS:
		raise ValueError(f"未知模型: {name}")
	return MODEL_BUILDERS[name]()


__all__ = [
	"ModelName",
	"get_available_model",
]
