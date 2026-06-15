from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, status

from app.sales.entrypoints.schemas import RegisterSaleRequest, SaleResponse

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
def register_sale(body: RegisterSaleRequest) -> SaleResponse:
    # FASE 1 — mock determinista alineado con el ejemplo del PRD
    # (2 remeras a 100 con costo 60 = total 200, ganancia bruta 80).
    return SaleResponse(
        id=uuid4(),
        total=Decimal("200.00"),
        total_paid=Decimal("200.00"),
        gross_profit=Decimal("80.00"),
    )
