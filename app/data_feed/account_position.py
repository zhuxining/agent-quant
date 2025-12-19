from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.prompt_build.account_prompt import build_account_prompt as format_account_prompt
from app.virtual_trade.account import AccountOverview, build_account_overview
from app.virtual_trade.position import list_position_overviews


async def build_account_prompt(
    session: AsyncSession,
    *,
    account_number: str,
    return_pct: float | Decimal | None = None,
    sharpe_ratio: float | Decimal | None = None,
) -> str:
    """拉取账户/持仓数据并组装账户快照 Markdown.

    - 绩效指标(收益率/夏普)可由上游计算后传入;缺失时用 None 填充。
    - 账户现金/市值/浮盈亏直接来自 virtual_trade.account 的聚合结果。
    - 持仓列表来自 virtual_trade.position 的 PositionOverview,并转成 prompt 结构。
    """

    account_overview: AccountOverview = await build_account_overview(
        session, account_number=account_number
    )
    positions = await list_position_overviews(session, account_number)

    position_dicts: list[dict[str, Any]] = [
        {
            "symbol": p.symbol_exchange,
            "quantity": p.quantity,
            "entry_price": p.average_cost,
            "current_price": p.market_price,
            "unrealized_pnl": p.unrealized_pnl,
            "profit_target": p.profit_target,
            "stop_loss": p.stop_loss,
            "confidence": p.notes or "N/A",
        }
        for p in positions
    ]

    total_market_value = sum((p.market_value for p in positions), start=Decimal("0"))
    total_unrealized_pnl = sum((p.unrealized_pnl for p in positions), start=Decimal("0"))

    return format_account_prompt(
        return_pct=return_pct if return_pct is not None else account_overview.return_pct,
        sharpe_ratio=sharpe_ratio if sharpe_ratio is not None else account_overview.sharpe_ratio,
        cash_available=account_overview.cash_available,
        positions=position_dicts,
        total_market_value=total_market_value,
        total_unrealized_pnl=total_unrealized_pnl,
    )


__all__ = ["build_account_prompt"]
