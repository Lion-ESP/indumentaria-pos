from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

# DTOs del lado cliente que espejan el contrato de /api. Decimal para todo lo
# monetario y de cantidades (la API serializa Decimal como string).


@dataclass(frozen=True)
class ProductInput:
    sku: str
    name: str
    unit: str
    cost_price: Decimal
    sale_price: Decimal
    initial_stock: Decimal = Decimal("0")


@dataclass(frozen=True)
class Product:
    id: UUID
    sku: str
    name: str
    unit: str
    cost_price: Decimal
    sale_price: Decimal
    stock: Decimal
    gross_margin_unit: Decimal


@dataclass(frozen=True)
class SaleLineInput:
    product_id: UUID
    quantity: Decimal


@dataclass(frozen=True)
class PaymentInput:
    method: str
    amount: Decimal
    installments_count: int = 1
    surcharge_rate: Decimal = Decimal("0")


@dataclass(frozen=True)
class SaleInput:
    lines: list[SaleLineInput] = field(default_factory=list)
    payments: list[PaymentInput] = field(default_factory=list)


@dataclass(frozen=True)
class Sale:
    id: UUID
    total: Decimal
    total_paid: Decimal
    gross_profit: Decimal


@dataclass(frozen=True)
class BalanceBucket:
    period: str
    gross_profit: Decimal
    net_profit: Decimal


@dataclass(frozen=True)
class Balance:
    total_gross_profit: Decimal
    total_net_profit: Decimal
    buckets: list[BalanceBucket] = field(default_factory=list)
