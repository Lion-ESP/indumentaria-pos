from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class BalanceBucket(BaseModel):
    period: str
    gross_profit: Decimal
    net_profit: Decimal


class BalanceResponse(BaseModel):
    from_date: date
    to_date: date
    group_by: str
    total_gross_profit: Decimal
    total_net_profit: Decimal
    buckets: list[BalanceBucket]
