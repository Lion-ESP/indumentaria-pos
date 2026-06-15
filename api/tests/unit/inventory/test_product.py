from __future__ import annotations

from decimal import Decimal

import pytest

from app.inventory.domain.entities import Product
from app.inventory.domain.exceptions import StockInsuficienteException
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


def _producto(stock: str = "10") -> Product:
    return Product(
        sku="REM-001",
        name="Remera",
        unit=UnitOfMeasure.UNIT,
        cost_price=Money(Decimal("60.00")),
        sale_price=Money(Decimal("100.00")),
        stock=Quantity(Decimal(stock), UnitOfMeasure.UNIT),
    )


@pytest.mark.unit
class TestProduct:
    def test_stock_por_defecto_es_cero_en_la_unidad(self) -> None:
        producto = Product(sku="X", name="X", unit=UnitOfMeasure.METER)
        assert producto.current_stock.value == Decimal("0")
        assert producto.current_stock.unit == UnitOfMeasure.METER

    def test_gross_margin_unit(self) -> None:
        assert _producto().gross_margin_unit.amount == Decimal("40.00")

    def test_can_fulfill(self) -> None:
        producto = _producto("10")
        assert producto.can_fulfill(Quantity(Decimal("10"), UnitOfMeasure.UNIT))
        assert not producto.can_fulfill(Quantity(Decimal("11"), UnitOfMeasure.UNIT))

    def test_decrease_stock_descuenta(self) -> None:
        producto = _producto("10")
        producto.decrease_stock(Quantity(Decimal("3"), UnitOfMeasure.UNIT))
        assert producto.current_stock.value == Decimal("7")

    def test_decrease_stock_insuficiente_lanza(self) -> None:
        producto = _producto("2")
        with pytest.raises(StockInsuficienteException) as exc_info:
            producto.decrease_stock(Quantity(Decimal("5"), UnitOfMeasure.UNIT))
        assert exc_info.value.sku == "REM-001"
        assert exc_info.value.requested == Decimal("5")

    def test_increase_stock_aumenta(self) -> None:
        producto = _producto("10")
        producto.increase_stock(Quantity(Decimal("5"), UnitOfMeasure.UNIT))
        assert producto.current_stock.value == Decimal("15")
