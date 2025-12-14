from __future__ import annotations

from decimal import Decimal
from textwrap import dedent
from typing import Any


def _fmt_number(value: float | Decimal | None, *, suffix: str = "") -> str:
    if value is None:
        return "N/A" + suffix
    try:
        return f"{float(value):.6g}{suffix}"
    except (TypeError, ValueError):
        return f"{value}{suffix}"


def _fmt_currency(value: float | Decimal | None) -> str:
    return f"${_fmt_number(value)}" if value is not None else "$N/A"


def _fmt_pct(value: float | Decimal | None) -> str:
    return _fmt_number(value, suffix="%")


def _build_positions_block(positions: list[dict[str, Any]]) -> str:
    if not positions:
        return "(无持仓)"

    blocks: list[str] = []
    for pos in positions:
        blocks.append(
            dedent(
                f"""
                {{
                  'symbol': '{pos.get("symbol", "?")}',
                  'quantity': {pos.get("quantity", "N/A")},
                  'entry_price': {pos.get("entry_price", "N/A")},
                  'current_price': {pos.get("current_price", "N/A")},
                  'unrealized_pnl': {pos.get("unrealized_pnl", "N/A")},
                  'exit_plan': {{
                    'profit_target': {pos.get("profit_target", "N/A")},
                    'stop_loss': {pos.get("stop_loss", "N/A")},
                  }},
                  'confidence': {pos.get("confidence", "N/A")},
                }},
                """
            ).strip()
        )

    return "\n".join(blocks)


def build_account_snapshot(
    *,
    return_pct: float | Decimal | None,
    sharpe_ratio: float | Decimal | None,
    cash_available: float | Decimal | None,
    positions: list[dict[str, Any]] | None = None,
    total_market_value: float | Decimal | None = None,
    total_unrealized_pnl: float | Decimal | None = None,
) -> str:
    """根据账户与持仓信息构建整齐的 Markdown 提示片段。"""

    positions = positions or []
    holding_symbols = "、".join([str(p.get("symbol", "?")) for p in positions]) or "暂无持仓"

    return dedent(
        f"""
        ## 账户与持仓信息

        **绩效指标:**

        - 当前收益率: {_fmt_pct(return_pct)}
        - 夏普率: {_fmt_number(sharpe_ratio)}

        **账户情况:**
        - 可用现金: {_fmt_currency(cash_available)}

        **当前实时仓位与表现:**
        当前持仓: {holding_symbols}
        合计市值: {_fmt_currency(total_market_value)}
        合计浮盈亏: {_fmt_currency(total_unrealized_pnl)}

        ```
        {_build_positions_block(positions)}
        ```
        """
    ).strip()


__all__ = ["build_account_snapshot"]
