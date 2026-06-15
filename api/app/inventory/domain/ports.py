from __future__ import annotations

from typing import Protocol


class PhotoStorage(Protocol):
    """Puerto de salida para almacenar fotos de producto."""

    def save(self, product_sku: str, content: bytes, filename: str) -> str:
        """Persiste el contenido y devuelve la ruta/URL resultante."""
        ...

    def delete(self, path: str) -> None: ...
