"""Formatting helpers used to render prompt sections."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from src.utils.utils import utc_now


def format_decimal(value: float | None, digits: int = 2) -> str:
	"""Format a single float value for prompt output."""
	if value is None:
		return "N/A"
	return f"{value:.{digits}f}"


def format_series(values: Sequence[float], digits: int = 3) -> str:
	"""Format a float sequence, typically time series data."""
	if not values:
		return "[]"
	formatted = ", ".join(f"{v:.{digits}f}" for v in values)
	return f"[{formatted}]"


def format_market_snapshot(snapshot: dict[str, Any]) -> str:
	"""Render a human friendly description of a market snapshot."""
	lines: list[str] = []
	lines.append(
		"current_price = {}, current_ema20 = {}, current_macd = {}, current_rsi(7) = {}".format(
			format_decimal(snapshot.get("current_price")),
			format_decimal(snapshot.get("current_ema20"), 3),
			format_decimal(snapshot.get("current_macd"), 3),
			format_decimal(snapshot.get("current_rsi7"), 3),
		)
	)

	price_change_1h = snapshot.get("price_change_1h")
	price_change_4h = snapshot.get("price_change_4h")
	if price_change_1h is not None or price_change_4h is not None:
		change_line = (
			f"Price Change: 1h = {format_decimal(price_change_1h, 2)}, "
			f"4h = {format_decimal(price_change_4h, 2)}"
		)
		lines.append(change_line)

	open_interest = snapshot.get("open_interest") or {}
	if open_interest:
		lines.append(
			"Open Interest => latest: {}, average: {}".format(
				format_decimal(open_interest.get("latest"), 3),
				format_decimal(open_interest.get("average"), 3),
			)
		)

	funding_rate = snapshot.get("funding_rate")
	if funding_rate is not None:
		lines.append(f"Funding Rate: {format_decimal(funding_rate, 6)}")

	short_term = snapshot.get("short_term") or {}
	lines.append("Short-term series (日线，旧→新):")
	lines.append(f"Mid prices: {format_series(short_term.get('mid_prices', []), 3)}")
	lines.append(f"EMA20: {format_series(short_term.get('ema20_values', []), 3)}")
	lines.append(f"MACD: {format_series(short_term.get('macd_values', []), 3)}")
	lines.append(f"RSI7: {format_series(short_term.get('rsi7_values', []), 3)}")
	lines.append(f"RSI14: {format_series(short_term.get('rsi14_values', []), 3)}")

	long_term = snapshot.get("long_term") or {}
	lines.append("Longer-term context (4小时周期):")
	lines.append(
		"EMA20 = {}, EMA50 = {}".format(
			format_decimal(long_term.get("ema20"), 3),
			format_decimal(long_term.get("ema50"), 3),
		)
	)
	lines.append(
		"ATR3 = {}, ATR14 = {}".format(
			format_decimal(long_term.get("atr3"), 3),
			format_decimal(long_term.get("atr14"), 3),
		)
	)
	lines.append(
		"Volume current = {}, Volume avg = {}".format(
			format_decimal(long_term.get("volume_current"), 3),
			format_decimal(long_term.get("volume_average"), 3),
		)
	)
	lines.append(f"MACD series: {format_series(long_term.get('macd_series', []), 3)}")
	lines.append(f"RSI14 series: {format_series(long_term.get('rsi14_series', []), 3)}")

	return "\n".join(lines)


def now_minutes_since(timestamp_ms: int | None) -> tuple[int, int] | None:
	"""Return elapsed hours and minutes since a millisecond timestamp."""
	if not timestamp_ms:
		return None
	current_ms = int(utc_now().timestamp() * 1000)
	delta_min = max((current_ms - timestamp_ms) // 60000, 0)
	return divmod(delta_min, 60)


__all__ = [
	"format_decimal",
	"format_series",
	"format_market_snapshot",
	"now_minutes_since",
]
