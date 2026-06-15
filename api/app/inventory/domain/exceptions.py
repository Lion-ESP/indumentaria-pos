from __future__ import annotations

from decimal import Decimal

from app.shared.domain.exceptions import DomainException, EntityNotFound


class ProductNotFound(EntityNotFound):
    code = "product_not_found"


class StockInsuficienteException(DomainException):
    code = "insufficient_stock"

    def __init__(self, sku: str, requested: Decimal, available: Decimal) -> None:
        super().__init__(
            f"Stock insuficiente para '{sku}': solicitado {requested}, disponible {available}"
        )
        self.sku = sku
        self.requested = requested
        self.available = available


class UnidadDeMedidaInvalida(DomainException):
    code = "invalid_unit_of_measure"
