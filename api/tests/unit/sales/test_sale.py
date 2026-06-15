from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from app.sales.domain.entities import (
    Installment,
    Payment,
    PaymentMethod,
    Sale,
    SaleLine,
)
from app.sales.domain.exceptions import CuotasInvalidasException, VentaNoCuadraException
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


def _linea(cantidad: str = "2") -> SaleLine:
    return SaleLine(
        product_id=uuid4(),
        sku="REM-001",
        quantity=Quantity(Decimal(cantidad), UnitOfMeasure.UNIT),
        unit_sale_price=Money(Decimal("100.00")),
        unit_cost_price=Money(Decimal("60.00")),
    )


@pytest.mark.unit
class TestSaleLine:
    def test_subtotal_costo_y_ganancia(self) -> None:
        linea = _linea("2")
        assert linea.subtotal.amount == Decimal("200.00")
        assert linea.line_cost.amount == Decimal("120.00")
        assert linea.gross_profit.amount == Decimal("80.00")


@pytest.mark.unit
class TestPayment:
    def test_total_con_recargo(self) -> None:
        payment = Payment(
            PaymentMethod.CREDIT_CARD,
            Money(Decimal("100.00")),
            surcharge_rate=Decimal("0.15"),
        )
        assert payment.total_with_surcharge.amount == Decimal("115.00")


@pytest.mark.unit
class TestInstallment:
    def test_es_un_value_object(self) -> None:
        cuota = Installment(number=1, amount=Money(Decimal("10.00")), due_date=date.today())
        assert cuota.number == 1


@pytest.mark.unit
class TestSale:
    def test_totales_y_ganancia(self) -> None:
        sale = Sale(lines=[_linea("2")])
        assert sale.total.amount == Decimal("200.00")
        assert sale.gross_profit.amount == Decimal("80.00")

    def test_validate_ok_cuando_cuadra(self) -> None:
        sale = Sale(
            lines=[_linea("2")],
            payments=[Payment(PaymentMethod.CASH, Money(Decimal("200.00")))],
        )
        sale.validate()

    def test_validate_sin_lineas_lanza(self) -> None:
        with pytest.raises(VentaNoCuadraException, match="no tiene líneas"):
            Sale().validate()

    def test_validate_pagos_no_cuadran_lanza(self) -> None:
        sale = Sale(
            lines=[_linea("2")],
            payments=[Payment(PaymentMethod.CASH, Money(Decimal("150.00")))],
        )
        with pytest.raises(VentaNoCuadraException):
            sale.validate()

    def test_validate_cuotas_invalidas_lanza(self) -> None:
        sale = Sale(
            lines=[_linea("2")],
            payments=[
                Payment(
                    PaymentMethod.CREDIT_CARD,
                    Money(Decimal("200.00")),
                    installments_count=0,
                )
            ],
        )
        with pytest.raises(CuotasInvalidasException):
            sale.validate()
