from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends
from sqlmodel import Session

from app.sales.adapters.repositories import SqlSaleRepository
from app.sales.adapters.stock_adapter import InventoryStockAdapter
from app.sales.application.use_cases import RegisterSaleUseCase
from app.sales.domain.services import InstallmentCalculator
from app.shared.adapters.database import get_session, get_session_factory
from app.shared.adapters.unit_of_work import SqlUnitOfWork


def get_register_sale_use_case(
    session_factory: Callable[[], Session] = Depends(get_session_factory),
) -> RegisterSaleUseCase:
    uow = SqlUnitOfWork(session_factory)
    stock = InventoryStockAdapter(uow)
    return RegisterSaleUseCase(uow, stock, InstallmentCalculator())


def get_sale_repository(
    session: Session = Depends(get_session),
) -> SqlSaleRepository:
    return SqlSaleRepository(session)
