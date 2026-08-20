"""Shared Pydantic v2 building blocks.

CamelModel auto-converts snake_case Python field names to camelCase JSON keys
(alias) on the way out, and accepts either casing on the way in - this is
what makes our response bodies match client/lib/types.ts (`avgPrice`,
`pnlPercent`, `totalVolume`, etc.) without hand-writing an alias per field.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class Page(CamelModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    total: int | None = None


class ErrorDetail(CamelModel):
    code: str
    message: str
    details: dict | list | str | None = None


class ErrorResponse(CamelModel):
    error: ErrorDetail
