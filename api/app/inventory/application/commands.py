from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.shared.domain.quantity import UnitOfMeasure


@dataclass(frozen=True)
class CreateProductCommand:
    sku: str | None
    name: str
    unit: UnitOfMeasure
    cost_price: Decimal
    sale_price: Decimal
    initial_stock: Decimal = Decimal("0")


@dataclass(frozen=True)
class AdjustStockCommand:
    product_id: UUID
    delta: Decimal
