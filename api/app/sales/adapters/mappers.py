from __future__ import annotations

from app.sales.adapters.models import (
    InstallmentModel,
    PaymentModel,
    SaleLineModel,
    SaleModel,
)
from app.sales.domain.entities import (
    Installment,
    Payment,
    PaymentMethod,
    Sale,
    SaleLine,
)
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


def to_model(sale: Sale) -> SaleModel:
    return SaleModel(
        id=sale.id,
        created_at=sale.created_at,
        total=sale.total.amount,
        gross_profit=sale.gross_profit.amount,
        lines=[
            SaleLineModel(
                product_id=line.product_id,
                sku=line.sku,
                quantity_value=line.quantity.value,
                unit=line.quantity.unit.value,
                unit_sale_price=line.unit_sale_price.amount,
                unit_cost_price=line.unit_cost_price.amount,
            )
            for line in sale.lines
        ],
        payments=[
            PaymentModel(
                method=payment.method.value,
                amount=payment.amount.amount,
                installments_count=payment.installments_count,
                surcharge_rate=payment.surcharge_rate,
                installments=[
                    InstallmentModel(
                        number=installment.number,
                        amount=installment.amount.amount,
                        due_date=installment.due_date,
                    )
                    for installment in payment.installments
                ],
            )
            for payment in sale.payments
        ],
    )


def to_domain(row: SaleModel) -> Sale:
    sale = Sale(id=row.id, created_at=row.created_at)
    sale.lines = [
        SaleLine(
            product_id=line.product_id,
            sku=line.sku,
            quantity=Quantity(line.quantity_value, UnitOfMeasure(line.unit)),
            unit_sale_price=Money(line.unit_sale_price),
            unit_cost_price=Money(line.unit_cost_price),
        )
        for line in row.lines
    ]
    sale.payments = [
        Payment(
            method=PaymentMethod(payment.method),
            amount=Money(payment.amount),
            installments_count=payment.installments_count,
            surcharge_rate=payment.surcharge_rate,
            installments=[
                Installment(
                    number=installment.number,
                    amount=Money(installment.amount),
                    due_date=installment.due_date,
                )
                for installment in payment.installments
            ],
        )
        for payment in row.payments
    ]
    return sale
