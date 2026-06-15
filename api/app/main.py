from __future__ import annotations

from fastapi import FastAPI

from app.inventory.entrypoints.router import router as inventory_router
from app.reporting.entrypoints.router import router as reporting_router
from app.sales.entrypoints.router import router as sales_router
from app.shared.adapters.exception_handlers import register_exception_handlers


def create_app() -> FastAPI:
    app = FastAPI(title="indumentaria-pos", version="0.1.0")
    register_exception_handlers(app)
    app.include_router(inventory_router)
    app.include_router(sales_router)
    app.include_router(reporting_router)
    return app


app = create_app()
