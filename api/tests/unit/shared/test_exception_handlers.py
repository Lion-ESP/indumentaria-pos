from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import get_settings
from app.inventory.domain.exceptions import ProductNotFound, StockInsuficienteException
from app.sales.domain.exceptions import VentaNoCuadraException
from app.shared.adapters.exception_handlers import (
    _resolve_status,
    register_exception_handlers,
)
from app.shared.domain.exceptions import DomainException


@pytest.mark.unit
class TestResolveStatus:
    def test_entity_not_found_es_404(self) -> None:
        assert _resolve_status(ProductNotFound("x")) == 404

    def test_stock_insuficiente_es_409(self) -> None:
        exc = StockInsuficienteException("SKU", Decimal("5"), Decimal("2"))
        assert _resolve_status(exc) == 409

    def test_venta_no_cuadra_es_422(self) -> None:
        assert _resolve_status(VentaNoCuadraException("x")) == 422

    def test_domain_generica_es_400(self) -> None:
        assert _resolve_status(DomainException("x")) == 400


@pytest.mark.unit
def test_handler_traduce_excepcion_a_json() -> None:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise StockInsuficienteException("REM-001", Decimal("5"), Decimal("2"))

    resp = TestClient(app).get("/boom")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "insufficient_stock"


@pytest.mark.unit
def test_settings_por_defecto() -> None:
    settings = get_settings()
    assert settings.database_url.startswith("sqlite")
