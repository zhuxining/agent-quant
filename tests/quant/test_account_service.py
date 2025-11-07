from __future__ import annotations

import pytest

from src.quant.accounts.models import Position
from src.quant.accounts.repository import InMemoryAccountRepository
from src.quant.accounts.services import (
	AccountService,
	InsufficientFundsError,
	InvalidSignalError,
	PositionShortfallError,
)
from src.quant.core.types import TradeSignal


def _make_service() -> AccountService:
	repository = InMemoryAccountRepository()
	service = AccountService(repository)
	service.initialize(cash=10_000.0)
	return service


def test_buy_signal_updates_cash_and_position() -> None:
	service = _make_service()
	signal = TradeSignal(symbol="AAPL.US", side="BUY", quantity=10, confidence=0.9)
	snapshot = service.apply_signal(signal, execution_price=100.0)

	assert pytest.approx(snapshot.cash) == 9_000.0
	position = snapshot.positions["AAPL.US"]
	assert position.quantity == 10
	assert position.avg_price == 100.0
	assert position.last_price == 100.0
	assert len(service.list_trades()) == 1


def test_sell_signal_realizes_profit_and_clears_position() -> None:
	service = AccountService(InMemoryAccountRepository())
	service.initialize(
		cash=1_000.0,
		positions=[Position(symbol="AAPL.US", quantity=5, avg_price=80.0)],
	)
	signal = TradeSignal(symbol="AAPL.US", side="SELL", quantity=5, confidence=0.8)
	snapshot = service.apply_signal(signal, execution_price=100.0)

	assert pytest.approx(snapshot.cash) == 1_500.0
	assert snapshot.positions == {}
	assert pytest.approx(snapshot.realized_pnl) == 100.0
	trade = service.list_trades()[0]
	assert pytest.approx(trade.realized_pnl) == 100.0


def test_sell_without_position_raises() -> None:
	service = _make_service()
	signal = TradeSignal(symbol="MSFT.US", side="SELL", quantity=1, confidence=0.5)
	with pytest.raises(PositionShortfallError):
		service.apply_signal(signal, execution_price=50.0)


def test_buy_without_cash_raises() -> None:
	service = AccountService(InMemoryAccountRepository())
	service.initialize(cash=50.0)
	signal = TradeSignal(symbol="TSLA.US", side="BUY", quantity=10, confidence=0.7)
	with pytest.raises(InsufficientFundsError):
		service.apply_signal(signal, execution_price=10.0)


def test_batch_signals_apply_in_order() -> None:
	service = _make_service()
	signals = [
		TradeSignal(symbol="AAPL.US", side="BUY", quantity=10, confidence=0.8),
		TradeSignal(symbol="AAPL.US", side="SELL", quantity=5, confidence=0.7),
	]
	pricing = {"AAPL.US": 100.0}
	snapshot = service.apply_signals(signals, pricing)

	assert pytest.approx(snapshot.cash) == 9_500.0
	assert pytest.approx(snapshot.positions["AAPL.US"].quantity) == 5
	assert len(service.list_trades()) == 2


def test_missing_price_raises_invalid_signal() -> None:
	service = _make_service()
	signal = TradeSignal(symbol="AAPL.US", side="SELL", quantity=1, confidence=0.6)
	with pytest.raises(InvalidSignalError):
		service.apply_signal(signal)
