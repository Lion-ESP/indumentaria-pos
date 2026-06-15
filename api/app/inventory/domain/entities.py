from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.inventory.domain.exceptions import StockInsuficienteException
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


@dataclass(eq=False)
class Product(AggregateRoot):
    sku: str = ""
    name: str = ""
    unit: UnitOfMeasure = UnitOfMeasure.UNIT
    cost_price: Money = field(default_factory=Money.zero)
    sale_price: Money = field(default_factory=Money.zero)
    stock: Quantity | None = None
    photo_path: str | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if self.stock is None:
            self.stock = Quantity(Decimal(0), self.unit)

    @property
    def current_stock(self) -> Quantity:
        assert self.stock is not None
        return self.stock

    @property
    def gross_margin_unit(self) -> Money:
        """Ganancia bruta por unidad = precio de venta - precio de costo."""
        return self.sale_price - self.cost_price

    def can_fulfill(self, requested: Quantity) -> bool:
        return self.current_stock.is_enough_for(requested)

    def decrease_stock(self, requested: Quantity) -> None:
        if not self.can_fulfill(requested):
            raise StockInsuficienteException(self.sku, requested.value, self.current_stock.value)
        self.stock = self.current_stock.subtract(requested)

    def increase_stock(self, amount: Quantity) -> None:
        self.stock = self.current_stock.add(amount)
