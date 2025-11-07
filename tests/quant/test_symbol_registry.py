from __future__ import annotations

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from src.models.symbol import SymbolCreate, SymbolRecord
from src.quant.data_pipeline.symbols import DatabaseSymbolRegistry


def test_database_symbol_registry_refresh(tmp_path: Path) -> None:
	engine = create_engine(f"sqlite:///{tmp_path / 'symbols.db'}", echo=False)
	SQLModel.metadata.create_all(engine)

	with Session(engine) as session:
		session.add(SymbolRecord(symbol="AAPL.US", display_name="Apple", priority=1))
		session.add(
			SymbolRecord(
				symbol="TSLA.US",
				display_name="Tesla",
				priority=5,
				is_active=False,
			)
		)
		session.commit()

	def session_factory() -> Session:
		return Session(engine)

	registry = DatabaseSymbolRegistry(session_factory=session_factory)

	active_symbols = registry.refresh()
	assert active_symbols == ["AAPL.US"]

	all_symbols = registry.refresh(include_inactive=True)
	assert all_symbols == ["TSLA.US", "AAPL.US"]


def test_symbol_create_normalizes_symbol() -> None:
	schema = SymbolCreate(symbol=" tsla.us ", display_name="Tesla")
	assert schema.symbol == "TSLA.US"
