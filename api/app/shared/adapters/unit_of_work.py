from __future__ import annotations

from collections.abc import Callable
from types import TracebackType

from sqlmodel import Session

from app.inventory.adapters.repositories import SqlProductRepository
from app.inventory.domain.repositories import ProductRepository
from app.sales.adapters.repositories import SqlSaleRepository
from app.sales.domain.repositories import SaleRepository


class SqlUnitOfWork:
    """Frontera transaccional concreta. Agrupa los repositorios sobre una única
    sesión, de modo que venta + descuento de stock se confirman o revierten
    atómicamente. Satisface estructuralmente InventoryUnitOfWork y SalesUnitOfWork.
    """

    products: ProductRepository
    sales: SaleRepository

    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> SqlUnitOfWork:
        self._session = self._session_factory()
        self.products = SqlProductRepository(self._session)
        self.sales = SqlSaleRepository(self._session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
