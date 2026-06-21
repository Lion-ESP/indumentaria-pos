from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.inventory.domain.entities import Product


class ProductRepository(Protocol):
    """Puerto de salida para persistir productos (lo implementa la capa adapters)."""

    def get(self, product_id: UUID) -> Product | None: ...

    def get_by_sku(self, sku: str) -> Product | None: ...

    def next_auto_sku_number(self) -> int: ...

    def list_active(self) -> list[Product]: ...

    def add(self, product: Product) -> None: ...

    def update(self, product: Product) -> None: ...
