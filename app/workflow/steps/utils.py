"""Step utilities."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def parse_step_input(
    raw_input: str | dict[str, Any] | list[Any] | BaseModel | Any | None,
) -> dict[str, Any]:
    """将 StepInput.input 转换为字典。"""
    if raw_input is None:
        return {}
    if isinstance(raw_input, dict):
        return raw_input
    if isinstance(raw_input, BaseModel):
        return raw_input.model_dump()
    return {}
