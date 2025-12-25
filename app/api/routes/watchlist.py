"""Watchlist 相关 API。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.core.deps import CurrentUserDep
from app.data_source import LongportWatchlistSource
from app.utils.exceptions import NotFoundException
from app.utils.responses import ResponseEnvelope, success_response

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistSecurityRead(BaseModel):
    symbol: str = Field(description="标的代码, 例如 700.HK")
    market: str = Field(description="市场标识, 例如 HK/US/CN")
    name: str = Field(description="标的名称")
    watched_price: float | None = Field(default=None, description="关注价")
    watched_at: datetime | None = Field(default=None, description="关注时间")

    model_config = ConfigDict(from_attributes=True)


class WatchlistGroupRead(BaseModel):
    id: int = Field(description="分组 ID")
    name: str = Field(description="分组名称")
    securities: list[WatchlistSecurityRead] = Field(default_factory=list, description="股票列表")

    model_config = ConfigDict(from_attributes=True)


class WatchlistGroupUpdate(BaseModel):
    name: str | None = Field(default=None, description="新的分组名称, 不修改可不传")
    securities: list[str] | None = Field(default=None, description="证券代码列表")
    mode: Literal["add", "remove", "replace"] | None = Field(
        default=None, description="更新模式: add/remove/replace"
    )


class WatchlistGroupCreate(BaseModel):
    name: str = Field(description="分组名称")
    securities: list[str] | None = Field(default=None, description="初始证券列表")


@router.get("/{group_id}", response_model=ResponseEnvelope[WatchlistGroupRead])
async def get_watchlist_group(group_id: int, current_user: CurrentUserDep):
    """根据分组 ID 查询该分组下的股票列表。"""

    source = LongportWatchlistSource()
    group = source.find_group(group_id)
    if group is None:
        raise NotFoundException(
            message="分组不存在", error_code="WATCHLIST_GROUP_NOT_FOUND", status_code=404
        )

    group_data = source.serialize_group(group)
    group_read = WatchlistGroupRead.model_validate(group_data)
    return success_response(data=group_read, message="查询成功")


@router.post("/", response_model=ResponseEnvelope[dict[str, int]])
async def create_watchlist_group(
    payload: WatchlistGroupCreate,
    current_user: CurrentUserDep,
):
    """创建新的自选分组。"""

    source = LongportWatchlistSource()
    group_id = source.create_group(name=payload.name, securities=payload.securities)
    return success_response(data={"id": group_id}, message="创建成功")


@router.put("/{group_id}", response_model=ResponseEnvelope[WatchlistGroupRead])
async def update_watchlist_group(
    group_id: int,
    payload: WatchlistGroupUpdate,
    current_user: CurrentUserDep,
):
    """更新分组名称或证券列表。"""

    source = LongportWatchlistSource()
    try:
        updated_group = source.update_group(
            group_id,
            name=payload.name,
            securities=payload.securities,
            mode=payload.mode,
        )
    except ValueError as exc:
        msg = str(exc)
        if "未找到分组" in msg:
            raise NotFoundException(
                message="分组不存在", error_code="WATCHLIST_GROUP_NOT_FOUND", status_code=404
            ) from exc
        raise HTTPException(status_code=400, detail=msg) from exc

    group_data = source.serialize_group(updated_group)
    group_read = WatchlistGroupRead.model_validate(group_data)
    return success_response(data=group_read, message="更新成功")
