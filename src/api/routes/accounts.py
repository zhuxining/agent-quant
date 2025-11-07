from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from src.core.deps import CurrentUserDep
from src.quant.accounts.models import Position
from src.quant.accounts.repository import SQLModelAccountRepository
from src.quant.accounts.services import AccountOverview, AccountService
from src.quant.core.types import AccountSnapshot, ExecutedTrade
from src.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/quant/accounts", tags=["quant-accounts"])


def get_account_service() -> AccountService:
	return AccountService(SQLModelAccountRepository())


AccountServiceDep = Annotated[AccountService, Depends(get_account_service)]


class PositionRead(BaseModel):
	"""API representation of a position."""

	model_config = ConfigDict(from_attributes=True)

	symbol: str
	quantity: float
	avg_price: float
	last_price: float | None = None

	@classmethod
	def from_position(cls, position: Position) -> PositionRead:
		return cls(
			symbol=position.symbol,
			quantity=position.quantity,
			avg_price=position.avg_price,
			last_price=position.last_price,
		)


class PositionSnapshotRead(BaseModel):
	"""Snapshot representation keyed by symbol."""

	model_config = ConfigDict(from_attributes=True)

	symbol: str
	quantity: float
	avg_price: float
	last_price: float | None = None


class AccountSnapshotRead(BaseModel):
	"""Pydantic model for account snapshots."""

	model_config = ConfigDict(from_attributes=True)

	cash: float
	realized_pnl: float
	timestamp: datetime
	positions: dict[str, PositionSnapshotRead]

	@classmethod
	def from_snapshot(cls, snapshot: AccountSnapshot) -> AccountSnapshotRead:
		return cls(
			cash=snapshot.cash,
			realized_pnl=snapshot.realized_pnl,
			timestamp=snapshot.timestamp,
			positions={
				symbol: PositionSnapshotRead(
					symbol=symbol,
					quantity=position.quantity,
					avg_price=position.avg_price,
					last_price=position.last_price,
				)
				for symbol, position in snapshot.positions.items()
			},
		)


class AccountOverviewRead(BaseModel):
	"""Overview payload for dashboards."""

	model_config = ConfigDict(from_attributes=True)

	account_id: str
	cash: float
	realized_pnl: float
	equity: float
	updated_at: datetime
	positions: list[PositionRead]

	@classmethod
	def from_overview(cls, overview: AccountOverview) -> AccountOverviewRead:
		return cls(
			account_id=overview.account_id,
			cash=overview.cash,
			realized_pnl=overview.realized_pnl,
			equity=overview.equity,
			updated_at=overview.updated_at,
			positions=[PositionRead.from_position(pos) for pos in overview.positions],
		)


class ExecutedTradeRead(BaseModel):
	"""Trade history record."""

	model_config = ConfigDict(from_attributes=True)

	symbol: str
	side: str
	quantity: float
	price: float
	realized_pnl: float
	executed_at: datetime
	metadata: dict[str, Any] | None = None

	@classmethod
	def from_trade(cls, trade: ExecutedTrade) -> ExecutedTradeRead:
		return cls(
			symbol=trade.symbol,
			side=trade.side,
			quantity=trade.quantity,
			price=trade.price,
			realized_pnl=trade.realized_pnl,
			executed_at=trade.executed_at,
			metadata=trade.metadata or {},
		)


@router.get("/snapshot", response_model=ResponseEnvelope[AccountSnapshotRead])
async def get_account_snapshot(
	service: AccountServiceDep,
	_: CurrentUserDep,
) -> ResponseEnvelope[AccountSnapshotRead]:
	snapshot = service.get_snapshot()
	return success_response(AccountSnapshotRead.from_snapshot(snapshot), message="查询成功")


@router.get("/overview", response_model=ResponseEnvelope[AccountOverviewRead])
async def get_account_overview(
	service: AccountServiceDep,
	_: CurrentUserDep,
) -> ResponseEnvelope[AccountOverviewRead]:
	overview = service.overview()
	return success_response(AccountOverviewRead.from_overview(overview), message="查询成功")


@router.get("/positions", response_model=ResponseEnvelope[list[PositionRead]])
async def list_positions(
	service: AccountServiceDep,
	_: CurrentUserDep,
) -> ResponseEnvelope[list[PositionRead]]:
	positions = [PositionRead.from_position(pos) for pos in service.list_positions()]
	return success_response(positions, message="查询成功")


@router.get("/trades", response_model=ResponseEnvelope[list[ExecutedTradeRead]])
async def list_trades(
	service: AccountServiceDep,
	_: CurrentUserDep,
	limit: int = Query(50, ge=1, le=500),
) -> ResponseEnvelope[list[ExecutedTradeRead]]:
	trades: Sequence[ExecutedTrade] = service.list_trades(limit=limit)
	return success_response(
		[ExecutedTradeRead.from_trade(trade) for trade in trades],
		message="查询成功",
	)
