from __future__ import annotations

from collections.abc import Callable, Iterator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

# Importar los modelos registra sus tablas en SQLModel.metadata (necesario para
# create_all y para el autogenerate de Alembic).
from app.inventory.adapters import models as _inventory_models  # noqa: F401
from app.sales.adapters import models as _sales_models  # noqa: F401


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def create_db_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    return create_engine(url, connect_args=_connect_args(url))


engine = create_db_engine()


def create_all(target_engine: Engine | None = None) -> None:
    SQLModel.metadata.create_all(target_engine or engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def get_session_factory() -> Callable[[], Session]:
    return lambda: Session(engine)
