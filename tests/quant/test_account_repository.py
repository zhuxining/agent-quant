from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from quant.accounts.repository import SQLModelAccountRepository
from quant.core.types import AccountSnapshot, ExecutedTrade, PositionSnapshot


@pytest.fixture()
def repo(tmp_path: Path) -> SQLModelAccountRepository:
    url = f"sqlite:///{tmp_path / 'account.db'}"
    engine = create_engine(url, echo=False)
    SQLModel.metadata.create_all(engine)

    def session_factory() -> Session:
        return Session(engine)

    return SQLModelAccountRepository(session_factory=session_factory)


def test_snapshot_round_trip(repo: SQLModelAccountRepository) -> None:
	snapshot = AccountSnapshot(
		cash=5_000.0,
		realized_pnl=250.0,
		positions={
			"AAPL.US": PositionSnapshot(
				symbol="AAPL.US",
				quantity=10,
				avg_price=120.0,
				last_price=125.0,
			)
		},
	)

	repo.save(snapshot)
	loaded = repo.load()

	assert loaded.cash == pytest.approx(5_000.0)
	assert loaded.realized_pnl == pytest.approx(250.0)
	assert "AAPL.US" in loaded.positions
	assert loaded.positions["AAPL.US"].avg_price == pytest.approx(120.0)


def test_trade_record_persists(repo: SQLModelAccountRepository) -> None:
	record = ExecutedTrade(symbol="AAPL.US", side="BUY", quantity=5, price=100.0, realized_pnl=0.0)
	repo.record_trade(record)

	history = repo.list_trades()
	assert len(history) == 1
	assert history[0].symbol == "AAPL.US"
	assert history[0].side == "BUY"
