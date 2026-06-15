from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class BalanceBucket:
    period: str
    gross_profit: Decimal
    net_profit: Decimal


@dataclass(frozen=True)
class Balance:
    total_gross_profit: Decimal
    total_net_profit: Decimal
    buckets: list[BalanceBucket] = field(default_factory=list)
