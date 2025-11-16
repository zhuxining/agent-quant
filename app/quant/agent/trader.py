from openai import OpenAI

from app.core.config import settings


def kimi_trader(
	system_prompt: str,
	user_prompt: str,
):
	"""
	docstring
	"""
	client = OpenAI(
		api_key=settings.KIMI_API_KEY,
		base_url=settings.KIMI_API_BASE_URL,
	)
	completion = client.chat.completions.create(
		model=settings.KIMI_MODEL,
		messages=[
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
		temperature=0.6,
		response_format={"type": "json_object"},
	)

	return completion.choices[0].message.content


def deepseek_trader(
	system_prompt: str,
	user_prompt: str,
):
	"""
	docstring
	"""
	client = OpenAI(
		api_key=settings.DEEPSEEK_API_KEY,
		base_url=settings.DEEPSEEK_API_BASE_URL,
	)
	completion = client.chat.completions.create(
		model=settings.DEEPSEEK_MODEL,
		messages=[
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt},
		],
		temperature=0.6,
		response_format={"type": "json_object"},
	)

	return completion.choices[0].message.content
