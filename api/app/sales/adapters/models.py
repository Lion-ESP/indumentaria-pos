from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

# OJO: este módulo NO usa `from __future__ import annotations`. Con anotaciones
# diferidas, SQLAlchemy no puede resolver los genéricos de Relationship
# (list[SaleLineModel]) y falla al inicializar el mapper.
_CASCADE = {"cascade": "all, delete-orphan"}


class SaleModel(SQLModel, table=True):
    __tablename__ = "sales"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: date
    total: Decimal = Field(max_digits=12, decimal_places=2)
    gross_profit: Decimal = Field(max_digits=12, decimal_places=2)

    lines: list["SaleLineModel"] = Relationship(
        back_populates="sale", sa_relationship_kwargs=_CASCADE
    )
    payments: list["PaymentModel"] = Relationship(
        back_populates="sale", sa_relationship_kwargs=_CASCADE
    )


class SaleLineModel(SQLModel, table=True):
    __tablename__ = "sale_lines"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sale_id: UUID = Field(foreign_key="sales.id", index=True)
    product_id: UUID
    sku: str
    quantity_value: Decimal = Field(max_digits=14, decimal_places=3)
    unit: str
    unit_sale_price: Decimal = Field(max_digits=12, decimal_places=2)
    unit_cost_price: Decimal = Field(max_digits=12, decimal_places=2)

    sale: SaleModel = Relationship(back_populates="lines")


class PaymentModel(SQLModel, table=True):
    __tablename__ = "payments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sale_id: UUID = Field(foreign_key="sales.id", index=True)
    method: str
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    installments_count: int
    surcharge_rate: Decimal = Field(max_digits=6, decimal_places=4)

    sale: SaleModel = Relationship(back_populates="payments")
    installments: list["InstallmentModel"] = Relationship(
        back_populates="payment", sa_relationship_kwargs=_CASCADE
    )


class InstallmentModel(SQLModel, table=True):
    __tablename__ = "installments"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    payment_id: UUID = Field(foreign_key="payments.id", index=True)
    number: int
    amount: Decimal = Field(max_digits=12, decimal_places=2)
    due_date: date

    payment: PaymentModel = Relationship(back_populates="installments")
