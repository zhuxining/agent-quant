from app.quant.agent.agno_client import run_quant_agent


def kimi_trader(
	system_prompt: str,
	user_prompt: str,
):
	"""调用 Kimi 配置的 agno Agent。"""

	return run_quant_agent(system_prompt, user_prompt, provider="kimi")


def deepseek_trader(
	system_prompt: str,
	user_prompt: str,
):
	"""调用 DeepSeek 配置的 agno Agent。"""

	return run_quant_agent(system_prompt, user_prompt, provider="deepseek")
