"""Utility classes for maintaining the tradable symbol universe."""

from __future__ import annotations

from collections.abc import Iterable, MutableSet


class SymbolRegistry:
    """In-memory registry of symbols to drive data ingestion."""

    def __init__(self, seed: Iterable[str] | None = None) -> None:
        self._symbols: MutableSet[str] = {symbol.upper() for symbol in seed or []}

    def list_all(self) -> list[str]:
        """Return the sorted list of configured symbols."""
        return sorted(self._symbols)

    def add(self, symbol: str) -> None:
        """Register a symbol."""
        self._symbols.add(symbol.upper())

    def remove(self, symbol: str) -> None:
        """Remove a symbol if it exists."""
        self._symbols.discard(symbol.upper())

    def clear(self) -> None:
        """Reset the registry."""
        self._symbols.clear()
