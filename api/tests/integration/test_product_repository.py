from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session

from app.inventory.adapters.repositories import SqlProductRepository
from app.inventory.domain.entities import Product
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


@pytest.mark.integration
def test_round_trip_preserva_fraccion_de_merceria(session: Session) -> None:
    repository = SqlProductRepository(session)
    cinta = Product(
        sku="CINTA-01",
        name="Cinta",
        unit=UnitOfMeasure.METER,
        cost_price=Money(Decimal("120.50")),
        sale_price=Money(Decimal("200.00")),
        stock=Quantity(Decimal("2.750"), UnitOfMeasure.METER),
    )
    repository.add(cinta)
    session.commit()

    recuperado = repository.get_by_sku("CINTA-01")
    assert recuperado is not None
    assert recuperado.current_stock.value == Decimal("2.750")
    assert recuperado.cost_price.amount == Decimal("120.50")
    assert recuperado.unit == UnitOfMeasure.METER


@pytest.mark.integration
def test_list_active_excluye_inactivos(session: Session) -> None:
    repository = SqlProductRepository(session)
    activo = Product(sku="ACT-01", name="Activo", unit=UnitOfMeasure.UNIT, active=True)
    inactivo = Product(sku="INA-01", name="Inactivo", unit=UnitOfMeasure.UNIT, active=False)
    repository.add(activo)
    repository.add(inactivo)
    session.commit()

    skus = {producto.sku for producto in repository.list_active()}
    assert skus == {"ACT-01"}


@pytest.mark.integration
def test_update_persiste_cambios_de_stock(session: Session) -> None:
    repository = SqlProductRepository(session)
    producto = Product(
        sku="REM-001",
        name="Remera",
        unit=UnitOfMeasure.UNIT,
        stock=Quantity(Decimal("10"), UnitOfMeasure.UNIT),
    )
    repository.add(producto)
    session.commit()

    producto.decrease_stock(Quantity(Decimal("3"), UnitOfMeasure.UNIT))
    repository.update(producto)
    session.commit()

    recuperado = repository.get(producto.id)
    assert recuperado is not None
    assert recuperado.current_stock.value == Decimal("7")
