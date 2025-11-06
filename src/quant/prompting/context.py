"""Prompt context dataclasses describing account and market state."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PositionInfo:
	"""Snapshot describing a single position that will be presented to the Agent."""

	symbol: str
	side: str
	quantity: float
	avg_price: float
	current_price: float | None = None
	position_value: float | None = None
	weight: float | None = None
	unrealized_pnl: float | None = None
	update_time_ms: int | None = None


@dataclass(slots=True)
class AccountInfo:
	"""Aggregated account metrics consumed by the prompt builder."""

	equity: float
	cash: float
	buying_power: float
	realized_pnl: float | None = None
	unrealized_pnl: float = 0.0


@dataclass(slots=True)
class CandidateSymbol:
	"""Candidate instrument sourced from watchlists or strategies."""

	symbol: str
	sources: Sequence[str] = field(default_factory=tuple)


@dataclass(slots=True)
class OITopData:
	"""Open interest leaderboard entry to assist decision making."""

	rank: int
	oi_delta_percent: float
	oi_delta_value: float
	price_delta_percent: float
	net_long: float
	net_short: float


@dataclass(slots=True)
class DecisionContext:
	"""Complete trading context delivered to the decision Agents."""

	current_time: str
	runtime_minutes: int
	call_count: int
	account: AccountInfo
	positions: Sequence[PositionInfo] = field(default_factory=tuple)
	candidate_symbols: Sequence[CandidateSymbol] = field(default_factory=tuple)
	market_data: dict[str, dict[str, Any]] = field(default_factory=dict)
	oi_top_map: dict[str, OITopData] = field(default_factory=dict)
	performance: dict[str, Any] | None = None


def load_candidate_symbols(path: Path) -> list[CandidateSymbol]:
	"""Load candidate symbols from a JSON file.

	The expected format is a list of objects with keys ``symbol`` and optional ``sources``.
	Invalid entries will be ignored.
	"""

	if not path.exists():
		return []
	try:
		raw = json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return []
	result: list[CandidateSymbol] = []
	for item in raw:
		symbol = item.get("symbol")
		if not symbol:
			continue
		sources = tuple(item.get("sources") or [])
		result.append(CandidateSymbol(symbol=symbol, sources=sources))
	return result
