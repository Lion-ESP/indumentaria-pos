from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class LineCommand:
    product_id: UUID
    quantity: Decimal


@dataclass(frozen=True)
class PaymentCommand:
    method: str
    amount: Decimal
    installments_count: int = 1
    surcharge_rate: Decimal = Decimal("0")


@dataclass(frozen=True)
class RegisterSaleCommand:
    lines: list[LineCommand] = field(default_factory=list)
    payments: list[PaymentCommand] = field(default_factory=list)
