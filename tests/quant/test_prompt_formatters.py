from __future__ import annotations

from datetime import timedelta

from src.quant.prompting.formatters import (
	format_decimal,
	format_market_snapshot,
	format_series,
	now_minutes_since,
)


def test_format_decimal_handles_none() -> None:
	assert format_decimal(None) == "N/A"
	assert format_decimal(1.2345, digits=2) == "1.23"


def test_format_series_formats_sequence() -> None:
	assert format_series([]) == "[]"
	assert format_series([1.0, 2.0], digits=1) == "[1.0, 2.0]"


def test_now_minutes_since_returns_elapsed_minutes(monkeypatch) -> None:
	from src.utils.utils import utc_now

	base = utc_now()
	future = int((base + timedelta(hours=1, minutes=15)).timestamp() * 1000)
	monkeypatch.setattr("src.quant.prompting.formatters.utc_now", lambda: base + timedelta(hours=2))
	assert now_minutes_since(future) == (0, 45)
	assert now_minutes_since(None) is None


def test_format_market_snapshot_includes_core_fields() -> None:
	snapshot = {
		"current_price": 100.1234,
		"current_ema20": 98.5,
		"current_macd": 0.123,
		"current_rsi7": 55.6,
		"short_term": {"mid_prices": [1, 2, 3]},
		"long_term": {},
	}
	text = format_market_snapshot(snapshot)
	assert "current_price = 100.12" in text
	assert "Short-term series" in text
