from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    name: str = Field(min_length=1)
    unit: str = Field(pattern="^(unit|meter|kg)$")
    cost_price: Decimal = Field(ge=0)
    sale_price: Decimal = Field(ge=0)
    initial_stock: Decimal = Field(ge=0, default=Decimal("0"))


class ProductResponse(BaseModel):
    id: UUID
    sku: str
    name: str
    unit: str
    cost_price: Decimal
    sale_price: Decimal
    stock: Decimal
    gross_margin_unit: Decimal


class AdjustStockRequest(BaseModel):
    delta: Decimal
