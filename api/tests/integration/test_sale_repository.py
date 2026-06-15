from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.sales.adapters.repositories import SqlSaleRepository
from app.sales.domain.entities import Installment, Payment, PaymentMethod, Sale, SaleLine
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


@pytest.mark.integration
def test_round_trip_de_venta_con_lineas_pagos_y_cuotas(session: Session) -> None:
    repository = SqlSaleRepository(session)
    sale = Sale(
        lines=[
            SaleLine(
                product_id=uuid4(),
                sku="REM-001",
                quantity=Quantity(Decimal("2"), UnitOfMeasure.UNIT),
                unit_sale_price=Money(Decimal("100.00")),
                unit_cost_price=Money(Decimal("60.00")),
            )
        ],
        payments=[
            Payment(
                method=PaymentMethod.CREDIT_CARD,
                amount=Money(Decimal("200.00")),
                installments_count=3,
                surcharge_rate=Decimal("0"),
                installments=[
                    Installment(1, Money(Decimal("66.67")), date(2026, 1, 1)),
                    Installment(2, Money(Decimal("66.67")), date(2026, 2, 1)),
                    Installment(3, Money(Decimal("66.66")), date(2026, 3, 1)),
                ],
            )
        ],
    )
    repository.add(sale)
    session.commit()

    recuperada = repository.get(sale.id)
    assert recuperada is not None
    assert recuperada.total.amount == Decimal("200.00")
    assert recuperada.gross_profit.amount == Decimal("80.00")
    assert len(recuperada.lines) == 1
    assert recuperada.lines[0].quantity.value == Decimal("2")
    assert len(recuperada.payments[0].installments) == 3
