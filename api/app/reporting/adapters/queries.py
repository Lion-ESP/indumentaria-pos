from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.reporting.application.read_models import Balance, BalanceBucket
from app.sales.adapters.models import SaleModel


class SqlBalanceQuery:
    """Read model de balance: agrega la ganancia de las ventas del período.

    La ganancia neta hoy iguala a la bruta (aún no hay egresos/gastos
    registrados); el modelo ya deja el campo separado para cuando existan.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def balance(self, from_date: date, to_date: date, group_by: str = "day") -> Balance:
        rows = self._session.exec(
            select(SaleModel).where(
                SaleModel.created_at >= from_date,
                SaleModel.created_at <= to_date,
            )
        ).all()

        per_bucket: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        total = Decimal("0.00")
        for sale in rows:
            total += sale.gross_profit
            per_bucket[self._bucket_key(sale.created_at, group_by)] += sale.gross_profit

        buckets = [
            BalanceBucket(period=period, gross_profit=value, net_profit=value)
            for period, value in sorted(per_bucket.items())
        ]
        return Balance(total_gross_profit=total, total_net_profit=total, buckets=buckets)

    @staticmethod
    def _bucket_key(created_at: date, group_by: str) -> str:
        if group_by == "month":
            return created_at.strftime("%Y-%m")
        return created_at.isoformat()
