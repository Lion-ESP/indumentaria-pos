from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ProductModel(SQLModel, table=True):
    __tablename__ = "products"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sku: str = Field(index=True, unique=True)
    name: str
    unit: str
    cost_price: Decimal = Field(max_digits=12, decimal_places=2)
    sale_price: Decimal = Field(max_digits=12, decimal_places=2)
    stock_value: Decimal = Field(max_digits=14, decimal_places=3)
    photo_path: str | None = Field(default=None)
    active: bool = Field(default=True)
