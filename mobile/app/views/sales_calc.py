"""Cálculo puro del total de venta y del vuelto, sin estado ni Flet.

La cuantización a centavos replica la de `Money` en el backend (half-up), de modo
que el total que el frontend usa como pago coincide con el total que el dominio
recalcula desde el precio de catálogo y la venta cuadra.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


def line_total(unit_price: Decimal, quantity: Decimal) -> Decimal:
    """Total de una línea (precio × cantidad) cuantizado a centavos."""
    return (unit_price * quantity).quantize(CENTS, rounding=ROUND_HALF_UP)


def change_due(total: Decimal, received: Decimal) -> Decimal:
    """Diferencia recibido − total: positivo = vuelto, negativo = faltante."""
    return (received - total).quantize(CENTS, rounding=ROUND_HALF_UP)
