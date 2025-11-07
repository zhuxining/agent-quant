"""Backtest engine adapters."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import quantstats as qs
from loguru import logger

from quant.core.types import BacktestReport, TradeSignal


@dataclass(slots=True)
class BacktestEngineConfig:
	"""Configuration for the Quantstats backtest engine."""

	initial_capital: float = 100_000.0
	report_dir: Path = Path("logs/backtests")
	report_title: str = "Agent Quant Backtest"
	benchmark: str | None = None
	render_report: bool = True

	def __post_init__(self) -> None:
		self.report_dir = Path(self.report_dir)
		self.report_dir.mkdir(parents=True, exist_ok=True)


class QuantstatsBacktestEngine:
	"""Generate Quantstats reports from simulated executions."""

	def __init__(self, config: BacktestEngineConfig | None = None) -> None:
		self._config = config or BacktestEngineConfig()

	def run(self, signals: Iterable[TradeSignal]) -> BacktestReport:
		"""Simulate trade fills, compute metrics, and render Quantstats reports."""
		history = [signal for signal in signals if signal.quantity > 0]
		if not history:
			now = datetime.now(UTC)
			return BacktestReport(
				started_at=now,
				ended_at=now,
				metrics={"signal_count": 0.0},
				artifacts={},
			)

		equity_curve, realized = _simulate_equity(history, self._config.initial_capital)
		returns = equity_curve.pct_change().fillna(0.0)

		started_at = equity_curve.index[0].to_pydatetime()
		ended_at = equity_curve.index[-1].to_pydatetime()
		report_path = self._config.report_dir / f"backtest_{started_at:%Y%m%d_%H%M%S}.html"

		if self._config.render_report:
			try:
				qs.reports.html(
					returns,
					benchmark=self._config.benchmark,
					output=str(report_path),
					title=self._config.report_title,
					download=False,
				)
			except Exception as exc:  # pragma: no cover - quantstats internals
				logger.warning("Quantstats report generation failed: %s", exc)
		else:
			report_path.write_text("<html><body>Report generation disabled.</body></html>")

		metrics = {
			"signal_count": float(len(history)),
			"total_return": _safe_float((equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1),
			"sharpe": _safe_float(qs.stats.sharpe(returns)),
			"cagr": _safe_float(qs.stats.cagr(returns)),
			"max_drawdown": _safe_float(qs.stats.max_drawdown(returns)),
			"win_rate": _calc_win_rate(realized),
		}

		return BacktestReport(
			started_at=started_at,
			ended_at=ended_at,
			metrics=metrics,
			artifacts={
				"html_report": str(report_path),
				"equity_curve": equity_curve.to_dict(),
			},
		)


def _simulate_equity(
	signals: list[TradeSignal],
	initial_capital: float,
) -> tuple[pd.Series, list[float]]:
	"""Return equity Series indexed by timestamps and sell-side realized PnL."""
	cash = initial_capital
	holdings: dict[str, dict[str, float]] = {}
	points: list[tuple[datetime, float]] = []
	realized: list[float] = []

	for idx, signal in enumerate(signals):
		side = signal.side.upper()
		if side not in {"BUY", "SELL"}:
			continue
		price = _resolve_price(signal)
		timestamp = _resolve_timestamp(signal, idx)
		holding = holdings.setdefault(
			signal.symbol,
			{"quantity": 0.0, "avg_price": 0.0, "last_price": price},
		)

		if side == "BUY":
			cost = price * signal.quantity
			cash -= cost
			total_cost = holding["avg_price"] * holding["quantity"] + cost
			holding["quantity"] += signal.quantity
			holding["avg_price"] = (
				total_cost / holding["quantity"] if holding["quantity"] else 0.0
			)
			holding["last_price"] = price
			realized.append(0.0)
		else:  # SELL
			quantity = signal.quantity
			cash += price * quantity
			profit = (price - holding["avg_price"]) * min(quantity, holding["quantity"])
			holding["quantity"] -= quantity
			holding["last_price"] = price
			if holding["quantity"] <= 0:
				holdings.pop(signal.symbol, None)
			realized.append(profit)

		equity = cash + sum(
			data["quantity"] * data["last_price"] for data in holdings.values()
		)
		points.append((timestamp, equity))

	if not points:
		now = datetime.now(UTC)
		return pd.Series([initial_capital], index=[now]), realized

	points.sort(key=lambda item: item[0])
	index = pd.Index([point[0] for point in points], name="timestamp")
	values = [point[1] for point in points]
	curve = pd.Series(values, index=index)
	start_anchor = index[0] - timedelta(minutes=1)
	initial = pd.Series([initial_capital], index=pd.Index([start_anchor], name="timestamp"))
	return pd.concat([initial, curve]).sort_index(), realized


def _resolve_price(signal: TradeSignal) -> float:
	price = (signal.metadata or {}).get("price")
	if price is None:
		msg = f"缺少 {signal.symbol} 的成交价格，无法执行回测"
		raise ValueError(msg)
	return float(price)


def _resolve_timestamp(signal: TradeSignal, idx: int) -> datetime:
	metadata = signal.metadata or {}
	value = metadata.get("timestamp")
	if isinstance(value, datetime):
		if value.tzinfo is None:
			return value.replace(tzinfo=UTC)
		return value.astimezone(UTC)
	if isinstance(value, str):
		try:
			return datetime.fromisoformat(value).astimezone(UTC)
		except ValueError:
			pass
	base = datetime.now(UTC).replace(microsecond=0)
	return base + timedelta(minutes=idx)


def _safe_float(value: float | int | None) -> float:
	"""Convert metric outputs to floats while handling NaN."""
	if value is None:
		return 0.0
	numeric = float(value)
	if math.isnan(numeric):
		return 0.0
	return numeric


def _calc_win_rate(realized: list[float]) -> float:
	profitable = [pnl for pnl in realized if pnl > 0]
	total = len([pnl for pnl in realized if pnl != 0.0])
	if not total:
		return 0.0
	return len(profitable) / total
