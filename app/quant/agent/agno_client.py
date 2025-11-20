"""Agno-backed quant trader client."""

from __future__ import annotations

from typing import Literal

from agno.agent import Agent, RunOutput
from agno.models.deepseek import DeepSeek
from agno.models.openai import OpenAIChat
from loguru import logger

from app.core.config import settings
from app.utils.exceptions import AppException

Provider = Literal["kimi", "deepseek"]


class AgentConfigError(AppException):
	status_code = 500
	error_code = "AGENT_CONFIG_ERROR"
	message = "大模型配置缺失"


class AgentCallError(AppException):
	status_code = 502
	error_code = "AGENT_CALL_FAILED"
	message = "调用大模型失败"


def run_quant_agent(
	system_prompt: str,
	user_prompt: str,
	*,
	provider: Provider | None = None,
) -> str:
	"""Run quant agent via agno and return string content."""

	selected_provider = provider or _default_provider()
	agent = _build_agent(system_prompt, provider=selected_provider)
	try:
		result = agent.run(user_prompt)
	except Exception as exc:
		logger.exception("调用 Agno Agent 失败 | provider={}", selected_provider)
		raise AgentCallError(detail=str(exc)) from exc

	if isinstance(result, RunOutput):
		return result.get_content_as_string()

	try:
		return result.get_content_as_string()
	except AttributeError:
		return str(result)


def _build_agent(system_prompt: str, *, provider: Provider) -> Agent:
	model = _build_model(provider)
	return Agent(
		id=f"quant-trader-{provider}",
		name="Quant Trader",
		model=model,
		system_message=system_prompt,
		add_datetime_to_context=True,
		markdown=False,
		parse_response=False,
	)


def _build_model(provider: Provider):
	if provider == "kimi":
		if not settings.KIMI_API_KEY or not settings.KIMI_MODEL:
			msg = "请配置 KIMI_API_KEY 与 KIMI_MODEL"
			raise AgentConfigError(msg)
		return OpenAIChat(
			id=settings.KIMI_MODEL,
			api_key=settings.KIMI_API_KEY,
			base_url=settings.KIMI_API_BASE_URL,
			temperature=0.6,
		)
	if provider == "deepseek":
		if not settings.DEEPSEEK_API_KEY or not settings.DEEPSEEK_MODEL:
			msg = "请配置 DEEPSEEK_API_KEY 与 DEEPSEEK_MODEL"
			raise AgentConfigError(msg)
		return DeepSeek(
			id=settings.DEEPSEEK_MODEL,
			api_key=settings.DEEPSEEK_API_KEY,
			base_url=settings.DEEPSEEK_API_BASE_URL,
			temperature=0.6,
		)
	msg = f"未知 provider: {provider}"
	raise AgentConfigError(msg)


def _default_provider() -> Provider:
	if settings.KIMI_API_KEY and settings.KIMI_MODEL:
		return "kimi"
	if settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_MODEL:
		return "deepseek"
	msg = "请配置 KIMI 或 DeepSeek 的 API Key 与模型名称"
	raise AgentConfigError(msg)
