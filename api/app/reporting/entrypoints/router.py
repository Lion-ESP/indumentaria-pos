from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends

from app.reporting.adapters.queries import SqlBalanceQuery
from app.reporting.entrypoints.dependencies import get_balance_query
from app.reporting.entrypoints.schemas import BalanceBucket, BalanceResponse

router = APIRouter(prefix="/reports", tags=["reporting"])


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    from_date: date,
    to_date: date,
    group_by: str = "day",
    query: SqlBalanceQuery = Depends(get_balance_query),
) -> BalanceResponse:
    balance = query.balance(from_date, to_date, group_by)
    return BalanceResponse(
        from_date=from_date,
        to_date=to_date,
        group_by=group_by,
        total_gross_profit=balance.total_gross_profit,
        total_net_profit=balance.total_net_profit,
        buckets=[
            BalanceBucket(
                period=bucket.period,
                gross_profit=bucket.gross_profit,
                net_profit=bucket.net_profit,
            )
            for bucket in balance.buckets
        ],
    )
