"""Lightweight synchronous event bus for quant lifecycle hooks."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Any

EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    """Simple pub/sub event bus used to decouple modules."""

    def __init__(self) -> None:
        self._handlers: defaultdict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event: str, handler: EventHandler) -> None:
        """Attach a handler to an event."""
        self._handlers[event].append(handler)

    def unsubscribe(self, event: str, handler: EventHandler) -> None:
        """Detach a handler; silently ignore missing handlers."""
        try:
            self._handlers[event].remove(handler)
        except ValueError:
            return

    def emit(self, event: str, payload: dict[str, Any]) -> None:
        """Emit an event to all subscribers."""
        for handler in list(self._handlers[event]):
            handler(payload)

    def listeners(self, event: str) -> Iterable[EventHandler]:
        """Return listeners registered for inspection and testing."""
        return tuple(self._handlers[event])
