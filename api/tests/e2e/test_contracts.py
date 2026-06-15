from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
def test_openapi_contiene_endpoints_del_contrato(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/products" in paths
    assert "/sales" in paths
    assert "/reports/balance" in paths


@pytest.mark.e2e
def test_create_product_cumple_response_model(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={
            "sku": "REM-001",
            "name": "Remera",
            "unit": "unit",
            "cost_price": "60.00",
            "sale_price": "100.00",
            "initial_stock": "10",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert {
        "id",
        "sku",
        "name",
        "unit",
        "cost_price",
        "sale_price",
        "stock",
        "gross_margin_unit",
    } <= body.keys()


@pytest.mark.e2e
def test_list_products_devuelve_coleccion(client: TestClient) -> None:
    resp = client.get("/products")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert {"id", "sku", "stock"} <= body[0].keys()


@pytest.mark.e2e
def test_get_product_por_id(client: TestClient) -> None:
    product_id = "11111111-1111-1111-1111-111111111111"
    resp = client.get(f"/products/{product_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == product_id


@pytest.mark.e2e
def test_adjust_stock_modifica_el_stock(client: TestClient) -> None:
    product_id = "11111111-1111-1111-1111-111111111111"
    resp = client.post(f"/products/{product_id}/stock", json={"delta": "5"})
    assert resp.status_code == 200
    assert Decimal(resp.json()["stock"]) == Decimal("15")


@pytest.mark.e2e
def test_create_product_rechaza_unidad_invalida(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={
            "sku": "X",
            "name": "X",
            "unit": "litros",
            "cost_price": "1",
            "sale_price": "2",
        },
    )
    assert resp.status_code == 422


@pytest.mark.e2e
def test_register_sale_contrato_y_negocio(client: TestClient) -> None:
    resp = client.post(
        "/sales",
        json={
            "lines": [{"product_id": str(uuid4()), "quantity": "2"}],
            "payments": [{"method": "cash", "amount": "200.00"}],
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert {"id", "total", "total_paid", "gross_profit"} <= body.keys()
    assert Decimal(body["total"]) == Decimal(body["total_paid"])
    assert Decimal(body["gross_profit"]) == Decimal("80.00")


@pytest.mark.e2e
def test_get_balance_cumple_response_model(client: TestClient) -> None:
    resp = client.get("/reports/balance?from_date=2026-01-01&to_date=2026-01-31")
    assert resp.status_code == 200
    body = resp.json()
    assert {
        "from_date",
        "to_date",
        "group_by",
        "total_gross_profit",
        "total_net_profit",
        "buckets",
    } <= body.keys()
