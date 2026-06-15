from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.sales.domain.entities import Sale


class SaleRepository(Protocol):
    """Puerto de salida para persistir ventas (lo implementa la capa adapters)."""

    def get(self, sale_id: UUID) -> Sale | None: ...

    def add(self, sale: Sale) -> None: ...
