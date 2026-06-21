"""Generación de SKUs autogenerados (prefijo + correlativo).

El SKU automático tiene forma ``ART-0001``: un prefijo fijo y un correlativo con
relleno de ceros. El correlativo lo provee el repositorio (máximo existente + 1);
aquí vive sólo el formato, que es regla de dominio.
"""

from __future__ import annotations

AUTO_SKU_PREFIX = "ART-"
_PADDING = 4


def format_auto_sku(number: int) -> str:
    return f"{AUTO_SKU_PREFIX}{number:0{_PADDING}d}"


def parse_auto_sku(sku: str) -> int | None:
    """Correlativo de un SKU autogenerado, o ``None`` si no sigue el patrón."""
    if not sku.startswith(AUTO_SKU_PREFIX):
        return None
    suffix = sku[len(AUTO_SKU_PREFIX) :]
    return int(suffix) if suffix.isdigit() else None
