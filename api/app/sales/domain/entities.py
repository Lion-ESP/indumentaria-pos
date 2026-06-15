from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from app.sales.domain.exceptions import CuotasInvalidasException, VentaNoCuadraException
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity


class PaymentMethod(StrEnum):
    CASH = "cash"
    DEBIT = "debit"
    CREDIT_CARD = "credit_card"
    TRANSFER = "transfer"


@dataclass(frozen=True, slots=True)
class Installment:
    """Una cuota de un pago con tarjeta de crédito."""

    number: int
    amount: Money
    due_date: date


@dataclass
class Payment:
    """Un pago dentro de una venta. Si es tarjeta en cuotas, se descompone."""

    method: PaymentMethod
    amount: Money
    installments_count: int = 1
    surcharge_rate: Decimal = Decimal("0")
    installments: list[Installment] = field(default_factory=list)

    @property
    def total_with_surcharge(self) -> Money:
        return self.amount.multiply(Decimal("1") + self.surcharge_rate)


@dataclass
class SaleLine:
    product_id: UUID
    sku: str
    quantity: Quantity
    unit_sale_price: Money
    unit_cost_price: Money

    @property
    def subtotal(self) -> Money:
        return self.unit_sale_price.multiply(self.quantity.value)

    @property
    def line_cost(self) -> Money:
        return self.unit_cost_price.multiply(self.quantity.value)

    @property
    def gross_profit(self) -> Money:
        return self.subtotal - self.line_cost


@dataclass(eq=False)
class Sale(AggregateRoot):
    created_at: date = field(default_factory=date.today)
    lines: list[SaleLine] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)

    @property
    def total(self) -> Money:
        total = Money.zero()
        for line in self.lines:
            total = total + line.subtotal
        return total

    @property
    def total_paid(self) -> Money:
        paid = Money.zero()
        for payment in self.payments:
            paid = paid + payment.amount
        return paid

    @property
    def gross_profit(self) -> Money:
        profit = Money.zero()
        for line in self.lines:
            profit = profit + line.gross_profit
        return profit

    def validate(self) -> None:
        """Invariante de agregado: la venta debe cuadrar y las cuotas ser válidas."""
        if not self.lines:
            raise VentaNoCuadraException("La venta no tiene líneas")
        if self.total_paid.amount != self.total.amount:
            raise VentaNoCuadraException(
                f"Pagos ({self.total_paid.amount}) != total ({self.total.amount})"
            )
        for payment in self.payments:
            if payment.installments_count < 1:
                raise CuotasInvalidasException("Cantidad de cuotas inválida")
