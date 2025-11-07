"""Prompt assembly utilities for decision-making Agents."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from quant.core.types import AccountSnapshot, IndicatorSnapshot, MarketBar, PromptPayload

from .context import DecisionContext, PositionInfo
from .formatters import format_decimal, format_market_snapshot, now_minutes_since

if TYPE_CHECKING:
	from quant.execution.logger import ExecutionLogger


class PromptBuilderService:
	"""Legacy prompt builder used for indicator summarisation."""

	def __init__(self, logger: ExecutionLogger | None = None) -> None:
		self._logger = logger

	def build(
		self,
		symbol: str,
		bars: Sequence[MarketBar],
		indicators: IndicatorSnapshot,
		account: AccountSnapshot,
		*,
		strategy_params: Mapping[str, str] | None = None,
	) -> PromptPayload:
		"""Construct a prompt string with relevant context."""
		latest_bar = bars[-1] if bars else None
		position = account.positions.get(symbol)
		position_size = position.quantity if position else 0.0
		avg_price = position.avg_price if position else 0.0
		lines = [
			f"Symbol: {symbol}",
			f"Latest close: {latest_bar.close if latest_bar else 'n/a'}",
			f"Cash balance: {account.cash}",
			f"Realized PnL: {account.realized_pnl}",
			f"Position size: {position_size}",
			f"Average cost: {avg_price}",
			"Indicators:",
		]
		for name, value in sorted(indicators.values.items()):
			lines.append(f"- {name}: {value}")

		metadata = {
			"symbol": symbol,
			"strategy_params": dict(strategy_params or {}),
			"indicator_count": len(indicators.values),
		}
		payload = PromptPayload(content="\n".join(lines), metadata=metadata)
		if self._logger:
			self._logger.log_prompt(payload)
		return payload


def build_system_prompt(account_equity: float) -> str:
	"""Generate system prompt describing objectives and constraints."""
	min_size = account_equity * 0.1
	max_size = account_equity * 0.2
	sections = [
		"你是独立的量化交易助理，负责根据最新的市场数据与账户状态给出交易建议。\n\n",
		"# 🎯 核心目标\n\n",
		"追求稳健回报与回撤控制，宁缺勿滥。\n\n",
		"# ⚖️ 风险控制\n\n",
		"- 只有在信号充分、风险回报比>1:3 时才建议交易\n",
		f"- 单笔仓位建议控制在账户净值的 10%-20%（约 {min_size:.0f}-{max_size:.0f} 单位）\n",
		"- 同一时间持仓数量控制在 3 个标的以内\n",
		"- 若论证结果不足或趋势模糊，直接给出“hold”或“wait”\n\n",
		"# 📋 工作流程\n\n",
		"1. 审视账户现金、已有仓位与浮动盈亏\n",
		"2. 综合市场数据（价格、均线、成交量、技术指标等）判断趋势与风险\n",
		"3. 输出明确的交易建议或保持观望的理由\n\n",
		"# 📤 输出格式\n\n",
		"先输出简要的中文思考，再给出 JSON 数组。示例：\n",
		"[{\"symbol\":\"XYZ\",\"action\":\"buy\",\"quantity\":100,\"reasoning\":\"日线突破、成交量放大\"}]\n\n",
		"允许的 action: buy / sell / hold / wait（hold 说明维持现有仓位，wait 表示无操作建议）。\n",
		"若 action 为 buy 或 sell，必须提供 quantity 与 reasoning，",
		"可视情况补充其他字段（如目标价、止损）。",
	]
	return "".join(sections)


def _format_account_section(ctx: DecisionContext) -> str:
	acct = ctx.account
	cash_ratio = (acct.cash / acct.equity * 100) if acct.equity else 0.0
	parts = [
		f"**账户**: 净值 {format_decimal(acct.equity, 2)}",
		f"现金 {format_decimal(acct.cash, 2)} ({cash_ratio:.1f}%)",
		f"可用资金 {format_decimal(acct.buying_power, 2)}",
		f"已实现盈亏 {format_decimal(acct.realized_pnl, 2)}",
		f"浮动盈亏 {format_decimal(acct.unrealized_pnl, 2)}",
	]
	return " | ".join(parts) + "\n"


def _format_position_line(idx: int, pos: PositionInfo) -> list[str]:
	parts: list[str] = [
		f"{idx}. {pos.symbol} {pos.side.upper()}",
		f"数量 {format_decimal(pos.quantity, 4)}",
		f"成本 {format_decimal(pos.avg_price, 4)}",
		f"当前价 {format_decimal(pos.current_price, 4)}",
		f"持仓市值 {format_decimal(pos.position_value, 2)}",
		f"权重 {format_decimal(pos.weight, 4)}",
		f"浮盈 {format_decimal(pos.unrealized_pnl, 2)}",
	]
	line = " | ".join(parts)
	duration = now_minutes_since(pos.update_time_ms)
	if duration:
		hours, minutes = duration
		line = f"{line} | 持仓{hours}小时{minutes}分钟" if hours else f"{line} | 持仓{minutes}分钟"
	return [line]


def build_user_prompt(ctx: DecisionContext) -> str:
	"""Render a user prompt using the decision context."""
	sections: list[str] = []
	time_line = (
		f"**时间**: {ctx.current_time} | **扫描序号**: #{ctx.call_count} | "
		f"**累计运行**: {ctx.runtime_minutes} 分钟\n"
	)
	sections.append(time_line)

	if ctx.market_data:
		first_symbol, first_snapshot = next(iter(ctx.market_data.items()))
		sections.append(
			"**核心标的 {}**: 价格 {} | EMA20 {} | MACD {} | RSI7 {}".format(
				first_symbol,
				format_decimal(first_snapshot.get("current_price"), 2),
				format_decimal(first_snapshot.get("current_ema20"), 2),
				format_decimal(first_snapshot.get("current_macd"), 4),
				format_decimal(first_snapshot.get("current_rsi7"), 2),
			)
		)

	sections.append(_format_account_section(ctx))
	sections.append(f"当前持仓数量: {len(ctx.positions)}\n")

	if ctx.positions:
		sections.append("## 当前持仓")
		for idx, pos in enumerate(ctx.positions, start=1):
			sections.extend(_format_position_line(idx, pos))
			snapshot = ctx.market_data.get(pos.symbol)
			if snapshot:
				sections.append(format_market_snapshot(snapshot))
				sections.append("")
	else:
		sections.append("**当前持仓**: 无\n")

	sections.append(f"## 候选标的 ({len(ctx.candidate_symbols)} 个)\n")
	displayed = 0
	for candidate in ctx.candidate_symbols:
		snapshot = ctx.market_data.get(candidate.symbol)
		if not snapshot:
			continue
		displayed += 1
		tags = ""
		if len(candidate.sources) > 1:
			tags = " (AI500 + OI_Top)"
		elif candidate.sources and candidate.sources[0] == "oi_top":
			tags = " (OI_Top 持仓增长)"
		sections.append(f"### {displayed}. {candidate.symbol}{tags}")
		sections.append(format_market_snapshot(snapshot))
		sections.append("")
	if displayed == 0:
		sections.append("候选标的暂无可用市场数据。\n")

	if ctx.performance and "sharpe_ratio" in ctx.performance:
		sections.append(f"## 📊 夏普比率: {format_decimal(ctx.performance['sharpe_ratio'], 2)}\n")

	sections.append("---\n请给出思维链分析，并输出JSON数组形式的交易决策。")
	return "\n".join(sections)


def build_decision_prompts(ctx: DecisionContext) -> dict[str, str]:
	"""Return system and user prompts from the provided context."""
	system_prompt = build_system_prompt(ctx.account.equity)
	user_prompt = build_user_prompt(ctx)
	return {"system": system_prompt, "user": user_prompt}


def build_messages(system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
	"""Convert prompts into chat-completion message format."""
	return [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": user_prompt},
	]
