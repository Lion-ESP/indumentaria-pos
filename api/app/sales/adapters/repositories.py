from __future__ import annotations

from uuid import UUID

from sqlmodel import Session

from app.sales.adapters import mappers
from app.sales.adapters.models import SaleModel
from app.sales.domain.entities import Sale


class SqlSaleRepository:
    """Implementa el Protocol SaleRepository sobre una sesión SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, sale_id: UUID) -> Sale | None:
        row = self._session.get(SaleModel, sale_id)
        return mappers.to_domain(row) if row else None

    def add(self, sale: Sale) -> None:
        self._session.add(mappers.to_model(sale))
