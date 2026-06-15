from __future__ import annotations

import calendar
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.sales.domain.entities import Installment, Payment, PaymentMethod
from app.sales.domain.exceptions import CuotasInvalidasException
from app.shared.domain.money import CENTS, Money


def add_months(start: date, months: int) -> date:
    """Suma `months` meses a una fecha, en stdlib puro (sin dateutil).

    Clampa el día al último día válido del mes destino (ej. 31-ene + 1 mes
    -> 28/29-feb). Se mantiene en el dominio para no depender de terceros.
    """
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(start.day, last_day))


class InstallmentCalculator:
    """Descompone un pago con tarjeta de crédito en N cuotas. La última cuota
    absorbe el centavo de redondeo para que Σ cuotas == monto total exacto."""

    def build(self, payment: Payment, first_due: date) -> list[Installment]:
        if payment.method != PaymentMethod.CREDIT_CARD:
            return []
        count = payment.installments_count
        if count < 1:
            raise CuotasInvalidasException("Cuotas debe ser >= 1")

        total = payment.total_with_surcharge.amount
        base = (total / count).quantize(CENTS, rounding=ROUND_HALF_UP)
        installments: list[Installment] = []
        accumulated = Decimal("0")
        for number in range(1, count + 1):
            amount = base if number < count else total - accumulated
            accumulated += amount
            installments.append(
                Installment(
                    number=number,
                    amount=Money(amount),
                    due_date=add_months(first_due, number - 1),
                )
            )
        return installments
