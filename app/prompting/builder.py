"""Prompt building utilities for Agent Trader."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from threading import Lock
from typing import Any
import uuid

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.market.data_feed import (
    DEFAULT_ADJUST,
    DEFAULT_LONG_TERM_COUNT,
    DEFAULT_SHORT_TERM_COUNT,
    DataFeed,
    FeedSlice,
)
from app.models import Position, PositionSide, PositionStatus, Stock, TradeAccount


class PromptBuilderError(RuntimeError):
    """Base error for prompt builder components."""


class SystemPromptProviderError(PromptBuilderError):
    """Base error for prompt provider issues."""


class MissingSystemPromptError(SystemPromptProviderError):
    """Raised when the system prompt file is missing or empty."""


class UserPromptProviderError(PromptBuilderError):
    """Raised when user prompt context cannot be assembled."""


class MissingTradeAccountError(UserPromptProviderError):
    """Raised when the requested trade account does not exist."""


@dataclass(slots=True)
class AccountSnapshot:
    """Immutable view of a trade account."""

    id: uuid.UUID
    name: str
    account_number: str | None
    buying_power: Decimal
    is_active: bool
    description: str | None


@dataclass(slots=True)
class PositionSnapshot:
    """Simplified position view for prompt composition."""

    id: uuid.UUID
    symbol: str
    stock_name: str
    side: PositionSide
    status: PositionStatus
    quantity: int
    available_quantity: int
    average_cost: Decimal
    market_price: Decimal | None
    market_value: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal


class SystemPromptProvider:
    """Load and cache the shared Agent system prompt."""

    def __init__(
        self,
        path: Path | None = None,
        *,
        encoding: str = "utf-8",
    ) -> None:
        self._path = path or Path(__file__).with_name("system_prompt.md")
        self._encoding = encoding
        self._override: str | None = None
        self._cached: str | None = None
        self._lock = Lock()

    def load(self, *, force_reload: bool = False) -> str:
        """Return the system prompt text, falling back to file contents."""

        if self._override is not None:
            return self._override
        with self._lock:
            if self._cached is not None and not force_reload:
                return self._cached
            text = self._read_prompt()
            self._cached = text
            return text

    def override(self, prompt: str | None) -> None:
        """Set or remove an in-memory override for the system prompt."""

        with self._lock:
            self._override = prompt.strip() if prompt is not None else None

    def _read_prompt(self) -> str:
        if not self._path.exists():
            raise MissingSystemPromptError(f"未找到 System Prompt 文件: {self._path}")
        text = self._path.read_text(encoding=self._encoding)
        if not text.strip():
            raise MissingSystemPromptError("System Prompt 文件内容为空")
        return text


class UserPromptProvider:
    """Assemble user prompt context with account, positions, and market data."""

    def __init__(self, data_feed: DataFeed | None = None) -> None:
        self.data_feed = data_feed or DataFeed()

    async def build(
        self,
        session: AsyncSession,
        *,
        account_number: str,
        symbols: Sequence[str],
        long_term_count: int = DEFAULT_LONG_TERM_COUNT,
        short_term_count: int = DEFAULT_SHORT_TERM_COUNT,
        adjust: Any = DEFAULT_ADJUST,
        end_date: datetime | None = None,
    ) -> str:
        """Return the user prompt string."""

        if not symbols:
            raise ValueError("symbols 不能为空")
        focus_symbols = list(dict.fromkeys(symbols))
        latest_prices: dict[str, Decimal | None] = {
            symbol: self.data_feed.get_latest_price(
                symbol=symbol,
                adjust=adjust,
                end_date=end_date,
            )
            for symbol in focus_symbols
        }
        account_task = asyncio.create_task(self._load_account(session, account_number))
        positions_task = asyncio.create_task(
            self._load_positions(
                session,
                account_number,
                latest_prices=latest_prices,
            ),
        )
        account, positions = await asyncio.gather(account_task, positions_task)
        market_sections = []
        for s in focus_symbols:
            slices = self.data_feed.build(
                symbol=s,
                long_term_count=long_term_count,
                short_term_count=short_term_count,
                adjust=adjust,
                end_date=end_date,
            )
            section = self._format_market_section(s, slices["short_term"], slices["long_term"])
            market_sections.append(section)

        market_text = "\n\n".join(market_sections)
        return self._render_prompt(account, positions, market_text)

    async def _load_account(self, session: AsyncSession, account_number: str) -> AccountSnapshot:
        result = await session.execute(
            select(TradeAccount).where(TradeAccount.account_number == account_number)
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise MissingTradeAccountError(f"账户 {account_number} 不存在")
        return AccountSnapshot(
            id=account.id,
            name=account.name,
            account_number=account.account_number,
            buying_power=account.buying_power,
            is_active=account.is_active,
            description=account.description,
        )

    async def _load_positions(
        self,
        session: AsyncSession,
        account_number: str,
        *,
        latest_prices: dict[str, Decimal | None],
    ) -> list[PositionSnapshot]:
        statement = (
            select(Position, Stock)
            .join(
                Stock,
                func.concat(Stock.symbol, ".", Stock.exchange) == Position.symbol_exchange,
            )
            .where(Position.account_number == account_number)
        )
        result = await session.execute(statement)
        pairs = result.all()
        return [
            self._to_position_snapshot(
                position,
                stock,
                latest_price=latest_prices.get(stock.symbol),
            )
            for position, stock in pairs
        ]

    def _to_position_snapshot(
        self,
        position: Position,
        stock: Stock,
        *,
        latest_price: Decimal | None,
    ) -> PositionSnapshot:
        market_price = position.market_price
        market_value = position.market_value
        unrealized = position.unrealized_pnl
        if latest_price is not None:
            market_price = latest_price
            qty = Decimal(position.quantity)
            market_value = latest_price * qty
            if position.side is PositionSide.SHORT:
                unrealized = (position.average_cost - latest_price) * qty
            else:
                unrealized = (latest_price - position.average_cost) * qty
        return PositionSnapshot(
            id=position.id,
            symbol=stock.symbol,
            stock_name=stock.name,
            side=position.side,
            status=position.status,
            quantity=position.quantity,
            available_quantity=position.available_quantity,
            average_cost=position.average_cost,
            market_price=market_price,
            market_value=market_value,
            unrealized_pnl=unrealized,
            realized_pnl=position.realized_pnl,
        )

    def _render_prompt(
        self,
        account: AccountSnapshot,
        positions: Iterable[PositionSnapshot],
        market_text: str,
    ) -> str:
        sections = [
            self._render_account_section(account),
            self._render_positions_section(list(positions)),
            self._render_market_section(market_text),
        ]
        return "\n\n".join(section for section in sections if section)

    def _render_account_section(self, account: AccountSnapshot) -> str:
        status = "启用" if account.is_active else "停用"
        lines = [
            "## Account Overview",
            f"账户: {account.name} ({account.id})",
            f"状态: {status} | 账号: {account.account_number or 'N/A'}",
            f"购买力: {self._format_decimal(account.buying_power)}",
        ]
        if account.description:
            lines.append(f"备注: {account.description}")
        return "\n".join(lines)

    def _render_positions_section(self, positions: list[PositionSnapshot]) -> str:
        lines = ["## Positions"]
        if not positions:
            lines.append("当前无持仓。")
            return "\n".join(lines)
        total_market_value = sum((pos.market_value for pos in positions), Decimal("0"))
        total_unrealized = sum((pos.unrealized_pnl for pos in positions), Decimal("0"))
        lines.append(
            f"合计市值: {self._format_decimal(total_market_value)} | "
            f"合计浮盈亏: {self._format_decimal(total_unrealized)}"
        )
        for idx, position in enumerate(positions, start=1):
            lines.append(
                f"{idx}. {position.symbol} ({position.stock_name}) | "
                f"{position.side.value.upper()} | 状态: {position.status.value}"
            )
            lines.append(
                "    "
                + (
                    f"数量: {position.quantity} | 可用: {position.available_quantity} | 均价: "
                    f"{self._format_decimal(position.average_cost)} | 现价: "
                    f"{self._format_decimal(position.market_price)}"
                )
            )
            lines.append(
                "    "
                + (
                    f"市值: {self._format_decimal(position.market_value)} | 浮盈亏: "
                    f"{self._format_decimal(position.unrealized_pnl)} | 已实现盈亏: "
                    f"{self._format_decimal(position.realized_pnl)}"
                )
            )
        return "\n".join(lines)

    def _render_market_section(self, market_text: str) -> str:
        return "\n".join(["## Market Overview", market_text])

    @staticmethod
    def _format_decimal(value: Decimal | float | None, digits: int = 2) -> str:
        if value is None:
            return "N/A"
        return f"{value:.{digits}f}"

    def _format_market_section(
        self,
        symbol: str,
        short_term: FeedSlice,
        long_term: FeedSlice,
    ) -> str:
        latest = short_term.latest
        # Note: long_term.frame["volume"] might be a Series, need to handle it safely
        volume_series = long_term.frame.get("volume", [])

        lines = [
            f"** {symbol} **",
            (
                '"current_price = '
                f"{self._format_number(latest['close'], 1)}, "
                f"current_ema20 = {self._format_number(latest.get('ema_20'))}, "
                f"current_macd = {self._format_number(latest.get('macd'))}, "
                f'current_rsi (7 period) = {self._format_number(latest.get("rsi_7"))}"'
            ),
            "",
            "**short-term context (1-h timeframe):**",
            "",
            f"Mid prices: {self._format_series(short_term.frame.get('mid_price', []))}",
            f"EMA indicators (20-period): {self._format_series(short_term.frame.get('ema_20', []))}",
            f"MACD indicators: {self._format_series(short_term.frame.get('macd', []))}",
            f"RSI indicators (7-Period): {self._format_series(short_term.frame.get('rsi_7', []))}",
            (
                "RSI indicators (14-Period): "
                f"{self._format_series(short_term.frame.get('rsi_14', []))}"
            ),
            "",
            "**Longer-term context (1-day timeframe):**",
            "",
            (
                "20-Period EMA: "
                f"{self._format_number(long_term.latest.get('ema_20'))} vs. 50-Period EMA: "
                f"{self._format_number(long_term.latest.get('ema_50'))}"
            ),
            (
                "3-Period ATR: "
                f"{self._format_number(long_term.latest.get('atr_3'))} vs. 14-Period ATR: "
                f"{self._format_number(long_term.latest.get('atr_14'))}"
            ),
            (
                "Current Volume: "
                f"{self._format_number(long_term.latest.get('volume'))} vs. Average Volume: "
                f"{self._format_number(self._mean(volume_series))}"
            ),
            f"MACD indicators: {self._format_series(long_term.frame.get('macd', []))}",
            f"RSI indicators (14-Period): {self._format_series(long_term.frame.get('rsi_14', []))}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _mean(series: Any) -> float | None:
        # Simple mean helper that handles pandas Series or list
        if hasattr(series, "dropna"):
            clean = series.dropna()
            return float(clean.mean()) if not clean.empty else None
        if isinstance(series, list) and series:
            return sum(series) / len(series)
        return None

    @staticmethod
    def _format_series(
        series: Any,
        digits: int = 3,
        count: int = 10,
    ) -> str:
        if hasattr(series, "dropna"):
            values = series.dropna().tail(count).tolist()
        else:
            values = list(series)[-count:]
        if not values:
            return "[]"
        formatted = ", ".join(f"{value:.{digits}f}" for value in values)
        return f"[{formatted}]"

    @staticmethod
    def _format_number(value: Any, digits: int = 3) -> str:
        number = UserPromptProvider._coerce_number(value)
        if number is None:
            return "N/A"
        return f"{number:.{digits}f}"

    @staticmethod
    def _coerce_number(value: Any) -> float | None:
        import pandas as pd

        if value is None:
            return None
        if isinstance(value, pd.Series):
            if value.empty:
                return None
            value = value.iloc[-1]
        if not pd.api.types.is_scalar(value):
            return None
        if pd.isna(value):
            return None
        return float(value)


__all__ = [
    "AccountSnapshot",
    "MissingSystemPromptError",
    "MissingTradeAccountError",
    "PositionSnapshot",
    "PromptBuilderError",
    "SystemPromptProvider",
    "SystemPromptProviderError",
    "UserPromptProvider",
    "UserPromptProviderError",
]
