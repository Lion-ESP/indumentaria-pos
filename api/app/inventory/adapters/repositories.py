from __future__ import annotations

from uuid import UUID

from sqlmodel import Session, select

from app.inventory.adapters import mappers
from app.inventory.adapters.models import ProductModel
from app.inventory.domain.entities import Product
from app.inventory.domain.sku import parse_auto_sku


class SqlProductRepository:
    """Implementa el Protocol ProductRepository sobre una sesión SQLModel."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, product_id: UUID) -> Product | None:
        row = self._session.get(ProductModel, product_id)
        return mappers.to_domain(row) if row else None

    def get_by_sku(self, sku: str) -> Product | None:
        row = self._session.exec(select(ProductModel).where(ProductModel.sku == sku)).first()
        return mappers.to_domain(row) if row else None

    def next_auto_sku_number(self) -> int:
        skus = self._session.exec(select(ProductModel.sku)).all()
        numbers = [n for sku in skus if (n := parse_auto_sku(sku)) is not None]
        return max(numbers) + 1 if numbers else 1

    def list_active(self) -> list[Product]:
        rows = self._session.exec(select(ProductModel).where(ProductModel.active)).all()
        return [mappers.to_domain(row) for row in rows]

    def add(self, product: Product) -> None:
        self._session.add(mappers.to_model(product))

    def update(self, product: Product) -> None:
        row = self._session.get(ProductModel, product.id)
        if row is None:
            self._session.add(mappers.to_model(product))
            return
        updated = mappers.to_model(product)
        row.sku = updated.sku
        row.name = updated.name
        row.unit = updated.unit
        row.cost_price = updated.cost_price
        row.sale_price = updated.sale_price
        row.stock_value = updated.stock_value
        row.photo_path = updated.photo_path
        row.active = updated.active
        self._session.add(row)
