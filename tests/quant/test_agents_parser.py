from __future__ import annotations

from src.quant.agents.parsers import parse_trade_suggestions


def test_parse_trade_suggestions_extracts_signals() -> None:
	text = '[{"symbol":"AAPL.US","action":"buy","quantity":10,"confidence":0.8}]'
	signals = parse_trade_suggestions(text)
	assert len(signals) == 1
	assert signals[0].symbol == "AAPL.US"
	assert signals[0].side == "BUY"
	assert signals[0].quantity == 10
	assert signals[0].confidence == 0.8


def test_parse_trade_suggestions_handles_invalid_entries() -> None:
	text = '[{"symbol":"MSFT.US","quantity":"x"},"oops",{}]'
	signals = parse_trade_suggestions(text)
	assert signals == []
