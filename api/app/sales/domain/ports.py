from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


@dataclass(frozen=True, slots=True)
class ProductPricing:
    """Datos del producto congelados al momento de la venta."""

    sku: str
    unit: UnitOfMeasure
    sale_price: Money
    cost_price: Money


class StockPort(Protocol):
    """Lo que el contexto 'sales' necesita de 'inventory', sin acoplarse a sus
    clases concretas. Lo implementa un adaptador en la capa adapters."""

    def get_pricing(self, product_id: UUID) -> ProductPricing:
        """Precios y unidad del producto congelados al momento de la venta.

        Lanza ProductNotFound si el producto no existe.
        """
        ...

    def decrease_stock(self, product_id: UUID, quantity: Quantity) -> None:
        """Descuenta stock; lanza StockInsuficienteException si no alcanza."""
        ...
