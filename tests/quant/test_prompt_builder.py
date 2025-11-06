from __future__ import annotations

from datetime import timedelta

from src.quant.prompting.builder import (
	build_decision_prompts,
	build_messages,
	build_system_prompt,
	build_user_prompt,
)
from src.quant.prompting.context import AccountInfo, CandidateSymbol, DecisionContext, PositionInfo
from src.utils.utils import utc_now


def _sample_context() -> DecisionContext:
	account = AccountInfo(
		equity=10000.0,
		cash=4000.0,
		buying_power=6000.0,
		realized_pnl=500.0,
		unrealized_pnl=150.0,
	)
	position = PositionInfo(
		symbol="AAPL.US",
		side="long",
		quantity=10,
		avg_price=150.0,
		current_price=155.0,
		position_value=1550.0,
		weight=0.15,
		unrealized_pnl=50.0,
		update_time_ms=int((utc_now() - timedelta(minutes=30)).timestamp() * 1000),
	)
	market_snapshot = {
		"current_price": 155.0,
		"current_ema20": 152.5,
		"current_macd": 0.42,
		"current_rsi7": 58.0,
		"short_term": {"mid_prices": [150.0, 152.0, 155.0]},
		"long_term": {},
	}
	ctx = DecisionContext(
		current_time="2024-06-15 10:00",
		runtime_minutes=120,
		call_count=5,
		account=account,
		positions=[position],
		candidate_symbols=[CandidateSymbol(symbol="MSFT.US", sources=("ai_pool",))],
		market_data={"AAPL.US": market_snapshot, "MSFT.US": market_snapshot},
		performance={"sharpe_ratio": 1.25},
	)
	return ctx


def test_build_system_prompt_mentions_position_limits() -> None:
	prompt = build_system_prompt(10000)
	assert "10%-20%" in prompt
	assert "JSON 数组" in prompt


def test_build_user_prompt_contains_account_and_positions() -> None:
	ctx = _sample_context()
	prompt = build_user_prompt(ctx)
	assert "净值 10000.00" in prompt
	assert "AAPL.US" in prompt
	assert "候选标的" in prompt


def test_build_decision_prompts_returns_system_and_user() -> None:
	ctx = _sample_context()
	prompts = build_decision_prompts(ctx)
	assert "system" in prompts and "user" in prompts


def test_build_messages_returns_openai_style_payload() -> None:
	messages = build_messages("system", "user")
	assert messages[0]["role"] == "system"
	assert messages[1]["content"] == "user"
