from __future__ import annotations

from types import TracebackType
from typing import Protocol

from app.inventory.domain.repositories import ProductRepository


class InventoryUnitOfWork(Protocol):
    """Frontera transaccional del contexto inventory. La implementación concreta
    (SQL) vive en la capa adapters; en los tests se sustituye por un doble."""

    products: ProductRepository

    def __enter__(self) -> InventoryUnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
