from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from app.inventory.application.commands import AdjustStockCommand, CreateProductCommand
from app.inventory.application.unit_of_work import InventoryUnitOfWork
from app.inventory.domain.entities import Product
from app.inventory.domain.exceptions import DuplicateSku, ProductNotFound
from app.inventory.domain.sku import format_auto_sku
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity


class CreateProductUseCase:
    def __init__(self, uow: InventoryUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateProductCommand) -> UUID:
        with self._uow:
            if command.sku:
                if self._uow.products.get_by_sku(command.sku) is not None:
                    raise DuplicateSku(command.sku)
                sku = command.sku
            else:
                sku = format_auto_sku(self._uow.products.next_auto_sku_number())
            product = Product(
                sku=sku,
                name=command.name,
                unit=command.unit,
                cost_price=Money(command.cost_price),
                sale_price=Money(command.sale_price),
                stock=Quantity(command.initial_stock, command.unit),
            )
            self._uow.products.add(product)
            self._uow.commit()
            return product.id


class AdjustStockUseCase:
    """Ajusta el stock de un producto (delta positivo o negativo)."""

    def __init__(self, uow: InventoryUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: AdjustStockCommand) -> None:
        with self._uow:
            product = self._uow.products.get(command.product_id)
            if product is None:
                raise ProductNotFound(f"Producto {command.product_id} no encontrado")
            amount = Quantity(abs(command.delta), product.unit)
            if command.delta >= Decimal("0"):
                product.increase_stock(amount)
            else:
                product.decrease_stock(amount)
            self._uow.products.update(product)
            self._uow.commit()
