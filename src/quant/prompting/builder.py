"""Prompt assembly using market, indicator, and account context."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from quant.core.types import AccountSnapshot, IndicatorSnapshot, MarketBar, PromptPayload


class PromptBuilderService:
    """Compose structured prompts for downstream Agents."""

    def build(
        self,
        symbol: str,
        bars: Sequence[MarketBar],
        indicators: IndicatorSnapshot,
        account: AccountSnapshot,
        *,
        strategy_params: Mapping[str, str] | None = None,
    ) -> PromptPayload:
        """Construct a prompt string with relevant context."""
        latest_bar = bars[-1] if bars else None
        lines = [
            f"Symbol: {symbol}",
            f"Latest close: {latest_bar.close if latest_bar else 'n/a'}",
            f"Cash balance: {account.cash}",
            f"Position size: {account.positions.get(symbol, 0.0)}",
            "Indicators:",
        ]
        for name, value in sorted(indicators.values.items()):
            lines.append(f"- {name}: {value}")

        metadata = {
            "symbol": symbol,
            "strategy_params": dict(strategy_params or {}),
            "indicator_count": len(indicators.values),
        }
        return PromptPayload(content="\n".join(lines), metadata=metadata)
