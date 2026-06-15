from __future__ import annotations

from types import TracebackType
from typing import Protocol

from app.sales.domain.repositories import SaleRepository


class SalesUnitOfWork(Protocol):
    """Frontera transaccional del contexto sales. La implementación concreta
    (SQL) vive en la capa adapters; en los tests se sustituye por un doble."""

    sales: SaleRepository

    def __enter__(self) -> SalesUnitOfWork: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
