"""Validation schemas for Agent responses."""

from __future__ import annotations

from collections.abc import Sequence

from pydantic import BaseModel, Field, ValidationError, model_validator

from src.quant.core.types import AgentResponse, TradeSignal


class AgentSignalModel(BaseModel):
    """Schema describing a single trade signal."""

    symbol: str
    side: str
    quantity: float = Field(..., gt=0)
    confidence: float = Field(..., ge=0, le=1)

    @model_validator(mode="after")
    def normalize_side(self) -> AgentSignalModel:
        """Ensure the side attribute is standardized."""
        normalized = self.side.upper()
        if normalized not in {"BUY", "SELL", "HOLD"}:
            msg = f"Unsupported side: {self.side}"
            raise ValueError(msg)
        self.side = normalized
        return self


class AgentResponseModel(BaseModel):
    """Top-level schema for an Agent response."""

    signals: list[AgentSignalModel]


class SignalValidatorService:
    """Convert AgentResponse objects into validated TradeSignal instances."""

    def validate(self, response: AgentResponse) -> Sequence[TradeSignal]:
        """Validate and normalize Agent output."""
        if response.signals:
            return response.signals

        raw_signals = response.metadata.get("signals", [])
        try:
            model = AgentResponseModel.model_validate({"signals": raw_signals})
        except ValidationError:
            return []

        return [
            TradeSignal(
                symbol=item.symbol,
                side=item.side,
                quantity=item.quantity,
                confidence=item.confidence,
            )
            for item in model.signals
        ]
