from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class SaleLineRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)


class PaymentRequest(BaseModel):
    method: str = Field(pattern="^(cash|debit|credit_card|transfer)$")
    amount: Decimal = Field(gt=0)
    installments_count: int = Field(ge=1, default=1)
    surcharge_rate: Decimal = Field(ge=0, default=Decimal("0"))


class RegisterSaleRequest(BaseModel):
    lines: list[SaleLineRequest] = Field(min_length=1)
    payments: list[PaymentRequest] = Field(min_length=1)


class SaleResponse(BaseModel):
    id: UUID
    total: Decimal
    total_paid: Decimal
    gross_profit: Decimal
