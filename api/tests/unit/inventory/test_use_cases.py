from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.inventory.application.commands import AdjustStockCommand, CreateProductCommand
from app.inventory.application.use_cases import (
    AdjustStockUseCase,
    CreateProductUseCase,
)
from app.inventory.domain.entities import Product
from app.inventory.domain.exceptions import DuplicateSku, ProductNotFound
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


@pytest.fixture
def uow() -> MagicMock:
    fake = MagicMock()
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False
    fake.products.get_by_sku.return_value = None
    return fake


@pytest.mark.unit
class TestCreateProductUseCase:
    def test_crea_persiste_y_commitea(self, uow: MagicMock) -> None:
        use_case = CreateProductUseCase(uow)
        command = CreateProductCommand(
            sku="CINTA-01",
            name="Cinta",
            unit=UnitOfMeasure.METER,
            cost_price=Decimal("120.50"),
            sale_price=Decimal("200.00"),
            initial_stock=Decimal("2.750"),
        )
        product_id = use_case.execute(command)

        assert product_id is not None
        uow.products.add.assert_called_once()
        uow.commit.assert_called_once()
        persisted = uow.products.add.call_args.args[0]
        assert persisted.current_stock.value == Decimal("2.750")

    def test_sku_duplicado_lanza_y_no_commitea(self, uow: MagicMock) -> None:
        existente = Product(
            sku="CINTA-01",
            name="Cinta",
            unit=UnitOfMeasure.METER,
            cost_price=Money(Decimal("120.50")),
            sale_price=Money(Decimal("200.00")),
            stock=Quantity(Decimal("1"), UnitOfMeasure.METER),
        )
        uow.products.get_by_sku.return_value = existente
        use_case = CreateProductUseCase(uow)
        command = CreateProductCommand(
            sku="CINTA-01",
            name="Cinta",
            unit=UnitOfMeasure.METER,
            cost_price=Decimal("120.50"),
            sale_price=Decimal("200.00"),
            initial_stock=Decimal("2.750"),
        )

        with pytest.raises(DuplicateSku):
            use_case.execute(command)
        uow.products.add.assert_not_called()
        uow.commit.assert_not_called()


@pytest.mark.unit
class TestAdjustStockUseCase:
    def test_incrementa_stock_con_delta_positivo(self, uow: MagicMock) -> None:
        producto = Product(
            sku="REM-001",
            name="Remera",
            unit=UnitOfMeasure.UNIT,
            cost_price=Money(Decimal("60.00")),
            sale_price=Money(Decimal("100.00")),
            stock=Quantity(Decimal("10"), UnitOfMeasure.UNIT),
        )
        uow.products.get.return_value = producto
        use_case = AdjustStockUseCase(uow)

        use_case.execute(AdjustStockCommand(product_id=producto.id, delta=Decimal("5")))

        assert producto.current_stock.value == Decimal("15")
        uow.commit.assert_called_once()

    def test_decrementa_stock_con_delta_negativo(self, uow: MagicMock) -> None:
        producto = Product(
            sku="REM-001",
            name="Remera",
            unit=UnitOfMeasure.UNIT,
            stock=Quantity(Decimal("10"), UnitOfMeasure.UNIT),
        )
        uow.products.get.return_value = producto
        use_case = AdjustStockUseCase(uow)

        use_case.execute(AdjustStockCommand(product_id=producto.id, delta=Decimal("-4")))

        assert producto.current_stock.value == Decimal("6")

    def test_producto_inexistente_lanza(self, uow: MagicMock) -> None:
        uow.products.get.return_value = None
        use_case = AdjustStockUseCase(uow)

        with pytest.raises(ProductNotFound):
            use_case.execute(AdjustStockCommand(product_id=uuid4(), delta=Decimal("1")))
        uow.commit.assert_not_called()
