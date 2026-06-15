from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter

from app.reporting.entrypoints.schemas import BalanceBucket, BalanceResponse

router = APIRouter(prefix="/reports", tags=["reporting"])


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    from_date: date,
    to_date: date,
    group_by: str = "day",
) -> BalanceResponse:
    # FASE 1 — mock determinista (incluye la venta del flujo crítico).
    return BalanceResponse(
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
        total_gross_profit=Decimal("80.00"),
        total_net_profit=Decimal("80.00"),
        buckets=[
            BalanceBucket(
                period=from_date.isoformat(),
                gross_profit=Decimal("80.00"),
                net_profit=Decimal("80.00"),
            )
        ],
    )
