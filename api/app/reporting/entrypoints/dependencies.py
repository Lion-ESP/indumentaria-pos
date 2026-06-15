from __future__ import annotations

from fastapi import Depends
from sqlmodel import Session

from app.reporting.adapters.queries import SqlBalanceQuery
from app.shared.adapters.database import get_session


def get_balance_query(session: Session = Depends(get_session)) -> SqlBalanceQuery:
    return SqlBalanceQuery(session)
