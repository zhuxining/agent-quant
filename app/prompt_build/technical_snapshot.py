from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from textwrap import dedent

from app.data_feed.technical_indicator import TechnicalSnapshot


def _fmt_number(value: float | Decimal | None) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


def _fmt_list(values: Iterable[float] | None) -> str:
    if not values:
        return ""
    return ", ".join(_fmt_number(v) for v in values)


def _build_single_snapshot_block(snapshot: TechnicalSnapshot) -> str:
    return dedent(
        f"""
		### ALL {snapshot.symbol} DATA

		**Current Snapshot:**

		- current_price = {_fmt_number(snapshot.current_price)}
		- current_ema20 = {_fmt_number(snapshot.current_ema20)}
		- current_macd = {_fmt_number(snapshot.current_macd)}
		- current_rsi (7 period) = {_fmt_number(snapshot.current_rsi7)}

		**Short-term Context (1-h intervals, oldest → latest):**

		Mid prices: [{_fmt_list(snapshot.short_term_mid_prices)}]
		EMA indicators (20-period): [{_fmt_list(snapshot.short_term_ema20)}]
		MACD indicators: [{_fmt_list(snapshot.short_term_macd)}]
		RSI indicators (7-Period): [{_fmt_list(snapshot.short_term_rsi7)}]
		RSI indicators (14-Period): [{_fmt_list(snapshot.short_term_rsi14)}]

		**Longer-term Context (1-d intervals, oldest → latest):**

		20-Period EMA: {_fmt_number(snapshot.long_term_ema20)} vs. 50-Period EMA: {_fmt_number(snapshot.long_term_ema50)}
		3-Period ATR: {_fmt_number(snapshot.long_term_atr3)} vs. 14-Period ATR: {_fmt_number(snapshot.long_term_atr14)}
		Current Volume: {_fmt_number(snapshot.long_term_volume_current)} vs. Average Volume: {_fmt_number(snapshot.long_term_volume_avg)}
		MACD indicators (4h): [{_fmt_list(snapshot.long_term_macd)}]
		RSI indicators (14-Period): [{_fmt_list(snapshot.long_term_rsi14)}]
		"""
    ).strip()


def build_technical_snapshots(snapshots: list[TechnicalSnapshot]) -> str:
    """根据行情摘要列表构建整齐的多标的技术面提示片段。"""

    if not snapshots:
        return "## 当前所有标的的市场数据\n\n(暂无可用数据)"

    blocks = [_build_single_snapshot_block(snapshot) for snapshot in snapshots]
    joined = "\n\n---\n\n".join(blocks)
    return dedent(
        f"""
		## 当前所有标的的市场数据

		{joined}
		"""
    ).strip()


__all__ = ["build_technical_snapshots"]
