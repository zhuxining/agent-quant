from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import select

from core.deps import CurrentUserDep, SessionDep, current_superuser
from src.models import SymbolCreate, SymbolRead, SymbolRecord, SymbolUpdate, User
from src.utils.exceptions import ConflictException, NotFoundException
from src.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/symbols", tags=["symbols"])

SuperuserDep = Annotated[User, Depends(current_superuser)]


async def _get_symbol_or_404(db: SessionDep, symbol_id: UUID) -> SymbolRecord:
	result = await db.execute(select(SymbolRecord).where(SymbolRecord.id == symbol_id))
	record = result.scalar_one_or_none()
	if record is None:
		raise NotFoundException(message="标的不存在", error_code="SYMBOL_NOT_FOUND")
	return record


@router.get("/", response_model=ResponseEnvelope[list[SymbolRead]])
async def list_symbols(
	db: SessionDep,
	_current_user: CurrentUserDep,
	is_active: bool | None = Query(
		default=None,
		description="若提供则按是否启用过滤",
	),
) -> ResponseEnvelope[list[SymbolRead]]:
	statement = select(SymbolRecord).order_by(SymbolRecord.priority.desc(), SymbolRecord.symbol)
	if is_active is not None:
		statement = statement.where(SymbolRecord.is_active.is_(is_active))
	result = await db.execute(statement)
	records = result.scalars().all()
	data = [SymbolRead.model_validate(record) for record in records]
	return success_response(data=data, message="查询成功")


@router.post("/", response_model=ResponseEnvelope[SymbolRead])
async def create_symbol(
	db: SessionDep,
	payload: SymbolCreate,
	_: SuperuserDep,
) -> ResponseEnvelope[SymbolRead]:
	existing = await db.execute(select(SymbolRecord).where(SymbolRecord.symbol == payload.symbol))
	if existing.scalar_one_or_none():
		raise ConflictException(message="标的已存在", error_code="SYMBOL_EXISTS")

	record = SymbolRecord(**payload.model_dump())
	db.add(record)
	await db.commit()
	await db.refresh(record)
	return success_response(data=SymbolRead.model_validate(record), message="创建成功")


@router.get("/{symbol_id}", response_model=ResponseEnvelope[SymbolRead])
async def get_symbol(
	db: SessionDep,
	symbol_id: UUID,
	_current_user: CurrentUserDep,
) -> ResponseEnvelope[SymbolRead]:
	record = await _get_symbol_or_404(db, symbol_id)
	return success_response(data=SymbolRead.model_validate(record), message="查询成功")


@router.patch("/{symbol_id}", response_model=ResponseEnvelope[SymbolRead])
async def update_symbol(
	db: SessionDep,
	symbol_id: UUID,
	payload: SymbolUpdate,
	_: SuperuserDep,
) -> ResponseEnvelope[SymbolRead]:
	record = await _get_symbol_or_404(db, symbol_id)
	update_data = payload.model_dump(exclude_unset=True)
	for key, value in update_data.items():
		setattr(record, key, value)
	db.add(record)
	await db.commit()
	await db.refresh(record)
	return success_response(data=SymbolRead.model_validate(record), message="更新成功")


@router.delete("/{symbol_id}", response_model=ResponseEnvelope[dict[str, bool]])
async def delete_symbol(
	db: SessionDep,
	symbol_id: UUID,
	_: SuperuserDep,
) -> ResponseEnvelope[dict[str, bool]]:
	record = await _get_symbol_or_404(db, symbol_id)
	await db.delete(record)
	await db.commit()
	return success_response(data={"deleted": True}, message="删除成功")
