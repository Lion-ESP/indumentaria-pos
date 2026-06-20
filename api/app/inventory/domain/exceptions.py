from __future__ import annotations

from decimal import Decimal

from app.shared.domain.exceptions import BusinessRuleViolation, DomainException, EntityNotFound


class ProductNotFound(EntityNotFound):
    code = "product_not_found"


class DuplicateSku(BusinessRuleViolation):
    code = "duplicate_sku"

    def __init__(self, sku: str) -> None:
        super().__init__(f"Ya existe un producto con el SKU '{sku}'")
        self.sku = sku


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
