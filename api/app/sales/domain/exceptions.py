from __future__ import annotations

from app.shared.domain.exceptions import DomainException


class VentaNoCuadraException(DomainException):
    """La suma de pagos no coincide con el total de la venta."""

    code = "payments_do_not_match_total"


class CuotasInvalidasException(DomainException):
    code = "invalid_installments"


class MetodoDePagoNoSoportado(DomainException):
    code = "unsupported_payment_method"
