from __future__ import annotations

from datetime import date
from uuid import UUID

from app.sales.application.commands import RegisterSaleCommand
from app.sales.application.unit_of_work import SalesUnitOfWork
from app.sales.domain.entities import Payment, PaymentMethod, Sale, SaleLine
from app.sales.domain.ports import StockPort
from app.sales.domain.services import InstallmentCalculator
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity


class RegisterSaleUseCase:
    """Registra una venta de forma transaccional y atómica:

    1. Construye el agregado Sale con precios congelados desde inventory.
    2. Descompone las cuotas de los pagos con tarjeta.
    3. Valida invariantes (la venta cuadra).
    4. Descuenta stock (puede lanzar StockInsuficienteException).
    5. Persiste todo dentro de una sola Unit of Work.
    """

    def __init__(
        self,
        uow: SalesUnitOfWork,
        stock: StockPort,
        installments: InstallmentCalculator,
    ) -> None:
        self._uow = uow
        self._stock = stock
        self._installments = installments

    def execute(self, command: RegisterSaleCommand) -> UUID:
        with self._uow:
            sale = Sale()
            for line in command.lines:
                pricing = self._stock.get_pricing(line.product_id)
                sale.lines.append(
                    SaleLine(
                        product_id=line.product_id,
                        sku=pricing.sku,
                        quantity=Quantity(line.quantity, pricing.unit),
                        unit_sale_price=pricing.sale_price,
                        unit_cost_price=pricing.cost_price,
                    )
                )

            for payment_cmd in command.payments:
                payment = Payment(
                    method=PaymentMethod(payment_cmd.method),
                    amount=Money(payment_cmd.amount),
                    installments_count=payment_cmd.installments_count,
                    surcharge_rate=payment_cmd.surcharge_rate,
                )
                payment.installments = self._installments.build(payment, date.today())
                sale.payments.append(payment)

            sale.validate()

            for sale_line in sale.lines:
                self._stock.decrease_stock(sale_line.product_id, sale_line.quantity)

            self._uow.sales.add(sale)
            self._uow.commit()
            return sale.id
