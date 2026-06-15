from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends
from sqlmodel import Session

from app.inventory.adapters.repositories import SqlProductRepository
from app.inventory.application.use_cases import AdjustStockUseCase, CreateProductUseCase
from app.shared.adapters.database import get_session, get_session_factory
from app.shared.adapters.unit_of_work import SqlUnitOfWork


def get_uow(
    session_factory: Callable[[], Session] = Depends(get_session_factory),
) -> SqlUnitOfWork:
    return SqlUnitOfWork(session_factory)


def get_create_product_use_case(
    uow: SqlUnitOfWork = Depends(get_uow),
) -> CreateProductUseCase:
    return CreateProductUseCase(uow)


def get_adjust_stock_use_case(
    uow: SqlUnitOfWork = Depends(get_uow),
) -> AdjustStockUseCase:
    return AdjustStockUseCase(uow)


def get_product_repository(
    session: Session = Depends(get_session),
) -> SqlProductRepository:
    return SqlProductRepository(session)
