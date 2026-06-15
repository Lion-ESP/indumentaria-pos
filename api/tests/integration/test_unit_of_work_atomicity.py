from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

import pytest
from sqlalchemy import Engine
from sqlmodel import Session

from app.inventory.adapters.repositories import SqlProductRepository
from app.inventory.domain.entities import Product
from app.inventory.domain.exceptions import StockInsuficienteException
from app.sales.adapters.repositories import SqlSaleRepository
from app.sales.adapters.stock_adapter import InventoryStockAdapter
from app.sales.application.commands import (
    LineCommand,
    PaymentCommand,
    RegisterSaleCommand,
)
from app.sales.application.use_cases import RegisterSaleUseCase
from app.sales.domain.services import InstallmentCalculator
from app.shared.adapters.unit_of_work import SqlUnitOfWork
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


def _seed_product(engine: Engine, stock: str) -> Product:
    producto = Product(
        sku="REM-001",
        name="Remera",
        unit=UnitOfMeasure.UNIT,
        cost_price=Money(Decimal("60.00")),
        sale_price=Money(Decimal("100.00")),
        stock=Quantity(Decimal(stock), UnitOfMeasure.UNIT),
    )
    with Session(engine) as session:
        SqlProductRepository(session).add(producto)
        session.commit()
    return producto


def _use_case(factory: Callable[[], Session]) -> RegisterSaleUseCase:
    uow = SqlUnitOfWork(factory)
    return RegisterSaleUseCase(uow, InventoryStockAdapter(uow), InstallmentCalculator())


@pytest.mark.integration
def test_venta_commitea_y_descuenta_stock(engine: Engine) -> None:
    producto = _seed_product(engine, "10")

    def factory() -> Session:
        return Session(engine)

    sale_id = _use_case(factory).execute(
        RegisterSaleCommand(
            lines=[LineCommand(producto.id, Decimal("2"))],
            payments=[PaymentCommand("cash", Decimal("200.00"))],
        )
    )

    with Session(engine) as session:
        assert SqlSaleRepository(session).get(sale_id) is not None
        recuperado = SqlProductRepository(session).get(producto.id)
        assert recuperado is not None
        assert recuperado.current_stock.value == Decimal("8")


@pytest.mark.integration
def test_rollback_no_persiste_venta_ni_toca_stock(engine: Engine) -> None:
    producto = _seed_product(engine, "1")

    def factory() -> Session:
        return Session(engine)

    with pytest.raises(StockInsuficienteException):
        _use_case(factory).execute(
            RegisterSaleCommand(
                lines=[LineCommand(producto.id, Decimal("5"))],
                payments=[PaymentCommand("cash", Decimal("500.00"))],
            )
        )

    with Session(engine) as session:
        recuperado = SqlProductRepository(session).get(producto.id)
        assert recuperado is not None
        assert recuperado.current_stock.value == Decimal("1")
