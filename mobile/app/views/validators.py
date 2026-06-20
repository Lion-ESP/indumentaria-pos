"""Validadores puros para los formularios de las vistas Flet.

Cada función recibe el texto crudo de un campo y devuelve un mensaje de error
listo para `TextField.error_text`, o `None` si el valor es válido. Son puros (sin
estado ni Flet), de modo que se prueban con tests unitarios y se reutilizan entre
vistas sin acoplar la validación a la UI.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation


def parse_decimal(value: str | None) -> Decimal | None:
    """Devuelve el `Decimal` del texto, o `None` si no es un número válido."""
    try:
        return Decimal((value or "").strip())
    except InvalidOperation:
        return None


def required(value: str | None) -> str | None:
    return None if value and value.strip() else "Completá este campo."


def positive_decimal(value: str | None) -> str | None:
    number = parse_decimal(value)
    if number is None:
        return "Debe ser un número."
    if number <= 0:
        return "Debe ser mayor a 0."
    return None


def non_negative_decimal(value: str | None) -> str | None:
    number = parse_decimal(value)
    if number is None:
        return "Debe ser un número."
    if number < 0:
        return "No puede ser negativo."
    return None


def sale_above_cost(cost_price: str | None, sale_price: str | None) -> str | None:
    """Regla de negocio entre campos: el precio de venta debe superar al de costo.

    Solo evalúa cuando ambos son números válidos; los errores de formato los
    reportan `positive_decimal` sobre cada campo.
    """
    cost = parse_decimal(cost_price)
    sale = parse_decimal(sale_price)
    if cost is None or sale is None:
        return None
    if sale <= cost:
        return "El precio de venta debe ser mayor al costo."
    return None


def iso_date(value: str | None) -> str | None:
    try:
        date.fromisoformat((value or "").strip())
    except ValueError:
        return "Usá el formato YYYY-MM-DD."
    return None


def date_range(from_value: str | None, to_value: str | None) -> str | None:
    """Valida que el rango sea coherente cuando ambas fechas son válidas."""
    if iso_date(from_value) or iso_date(to_value):
        return None
    start = date.fromisoformat((from_value or "").strip())
    end = date.fromisoformat((to_value or "").strip())
    if start > end:
        return "La fecha 'desde' no puede ser posterior a 'hasta'."
    return None
