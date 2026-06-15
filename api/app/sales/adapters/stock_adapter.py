from __future__ import annotations

from uuid import UUID

from app.inventory.application.unit_of_work import InventoryUnitOfWork
from app.inventory.domain.exceptions import ProductNotFound
from app.sales.domain.ports import ProductPricing
from app.shared.domain.quantity import Quantity


class InventoryStockAdapter:
    """Implementa el puerto StockPort de sales usando los repositorios de
    inventory sobre la MISMA Unit of Work, garantizando atomicidad entre la
    venta y el descuento de stock."""

    def __init__(self, uow: InventoryUnitOfWork) -> None:
        self._uow = uow

    def get_pricing(self, product_id: UUID) -> ProductPricing:
        product = self._uow.products.get(product_id)
        if product is None:
            raise ProductNotFound(f"Producto {product_id} no encontrado")
        return ProductPricing(
            sku=product.sku,
            unit=product.unit,
            sale_price=product.sale_price,
            cost_price=product.cost_price,
        )

    def decrease_stock(self, product_id: UUID, quantity: Quantity) -> None:
        product = self._uow.products.get(product_id)
        if product is None:
            raise ProductNotFound(f"Producto {product_id} no encontrado")
        product.decrease_stock(quantity)
        self._uow.products.update(product)
