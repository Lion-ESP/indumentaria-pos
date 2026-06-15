from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.inventory.domain.exceptions import StockInsuficienteException
from app.sales.application.commands import (
    LineCommand,
    PaymentCommand,
    RegisterSaleCommand,
)
from app.sales.application.use_cases import RegisterSaleUseCase
from app.sales.domain.exceptions import VentaNoCuadraException
from app.sales.domain.ports import ProductPricing
from app.sales.domain.services import InstallmentCalculator
from app.shared.domain.money import Money
from app.shared.domain.quantity import UnitOfMeasure


@pytest.fixture
def stock_port() -> MagicMock:
    port = MagicMock()
    port.get_pricing.return_value = ProductPricing(
        sku="REM-001",
        unit=UnitOfMeasure.UNIT,
        sale_price=Money(Decimal("100.00")),
        cost_price=Money(Decimal("60.00")),
    )
    return port


@pytest.fixture
def uow() -> MagicMock:
    fake = MagicMock()
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False
    return fake


def _use_case(uow: MagicMock, stock_port: MagicMock) -> RegisterSaleUseCase:
    return RegisterSaleUseCase(uow, stock_port, InstallmentCalculator())


@pytest.mark.unit
class TestRegisterSaleUseCase:
    def test_venta_valida_descuenta_stock_y_commitea(
        self, uow: MagicMock, stock_port: MagicMock
    ) -> None:
        product_id = uuid4()
        command = RegisterSaleCommand(
            lines=[LineCommand(product_id, Decimal("2"))],
            payments=[PaymentCommand("cash", Decimal("200.00"))],
        )

        sale_id = _use_case(uow, stock_port).execute(command)

        assert sale_id is not None
        stock_port.decrease_stock.assert_called_once()
        uow.sales.add.assert_called_once()
        uow.commit.assert_called_once()

    def test_venta_que_no_cuadra_no_descuenta_ni_commitea(
        self, uow: MagicMock, stock_port: MagicMock
    ) -> None:
        command = RegisterSaleCommand(
            lines=[LineCommand(uuid4(), Decimal("2"))],
            payments=[PaymentCommand("cash", Decimal("150.00"))],
        )

        with pytest.raises(VentaNoCuadraException):
            _use_case(uow, stock_port).execute(command)

        stock_port.decrease_stock.assert_not_called()
        uow.commit.assert_not_called()

    def test_propaga_stock_insuficiente_y_no_commitea(
        self, uow: MagicMock, stock_port: MagicMock
    ) -> None:
        stock_port.decrease_stock.side_effect = StockInsuficienteException(
            "REM-001", Decimal("2"), Decimal("1")
        )
        command = RegisterSaleCommand(
            lines=[LineCommand(uuid4(), Decimal("2"))],
            payments=[PaymentCommand("cash", Decimal("200.00"))],
        )

        with pytest.raises(StockInsuficienteException):
            _use_case(uow, stock_port).execute(command)

        uow.commit.assert_not_called()

    def test_descompone_cuotas_de_tarjeta(self, uow: MagicMock, stock_port: MagicMock) -> None:
        command = RegisterSaleCommand(
            lines=[LineCommand(uuid4(), Decimal("2"))],
            payments=[PaymentCommand("credit_card", Decimal("200.00"), installments_count=3)],
        )

        _use_case(uow, stock_port).execute(command)

        persisted_sale = uow.sales.add.call_args.args[0]
        assert len(persisted_sale.payments[0].installments) == 3
