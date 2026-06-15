from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

PRODUCT_KEYS = {
    "id",
    "sku",
    "name",
    "unit",
    "cost_price",
    "sale_price",
    "stock",
    "gross_margin_unit",
}


def _create_product(
    client: TestClient,
    sku: str = "REM-001",
    unit: str = "unit",
    stock: str = "10",
) -> dict:
    resp = client.post(
        "/products",
        json={
            "sku": sku,
            "name": "Remera",
            "unit": unit,
            "cost_price": "60.00",
            "sale_price": "100.00",
            "initial_stock": stock,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.mark.e2e
def test_openapi_contiene_endpoints_del_contrato(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/products", "/sales", "/reports/balance"} <= paths.keys()


@pytest.mark.e2e
def test_create_product_cumple_contrato(client: TestClient) -> None:
    body = _create_product(client)
    assert body.keys() >= PRODUCT_KEYS
    assert Decimal(body["stock"]) == Decimal("10")
    assert Decimal(body["gross_margin_unit"]) == Decimal("40.00")


@pytest.mark.e2e
def test_create_product_rechaza_unidad_invalida(client: TestClient) -> None:
    resp = client.post(
        "/products",
        json={"sku": "X", "name": "X", "unit": "litros", "cost_price": "1", "sale_price": "2"},
    )
    assert resp.status_code == 422


@pytest.mark.e2e
def test_get_y_list_product(client: TestClient) -> None:
    created = _create_product(client)
    detalle = client.get(f"/products/{created['id']}")
    assert detalle.status_code == 200
    assert detalle.json()["id"] == created["id"]

    listado = client.get("/products")
    assert listado.status_code == 200
    assert any(item["sku"] == "REM-001" for item in listado.json())


@pytest.mark.e2e
def test_get_product_inexistente_devuelve_404(client: TestClient) -> None:
    resp = client.get("/products/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "product_not_found"


@pytest.mark.e2e
def test_adjust_stock_modifica_el_stock(client: TestClient) -> None:
    created = _create_product(client, stock="10")
    resp = client.post(f"/products/{created['id']}/stock", json={"delta": "5"})
    assert resp.status_code == 200
    assert Decimal(resp.json()["stock"]) == Decimal("15")


@pytest.mark.e2e
def test_flujo_inventariar_vender_balance(client: TestClient) -> None:
    producto = _create_product(client, stock="10")

    venta = client.post(
        "/sales",
        json={
            "lines": [{"product_id": producto["id"], "quantity": "2"}],
            "payments": [{"method": "cash", "amount": "200.00"}],
        },
    )
    assert venta.status_code == 201, venta.text
    cuerpo = venta.json()
    assert {"id", "total", "total_paid", "gross_profit"} <= cuerpo.keys()
    assert Decimal(cuerpo["total"]) == Decimal(cuerpo["total_paid"])
    assert Decimal(cuerpo["gross_profit"]) == Decimal("80.00")

    detalle = client.get(f"/products/{producto['id']}")
    assert Decimal(detalle.json()["stock"]) == Decimal("8")

    balance = client.get("/reports/balance?from_date=2026-01-01&to_date=2030-12-31")
    assert balance.status_code == 200
    assert Decimal(balance.json()["total_gross_profit"]) == Decimal("80.00")


@pytest.mark.e2e
def test_venta_con_stock_insuficiente_devuelve_409(client: TestClient) -> None:
    producto = _create_product(client, stock="1")
    resp = client.post(
        "/sales",
        json={
            "lines": [{"product_id": producto["id"], "quantity": "5"}],
            "payments": [{"method": "cash", "amount": "500.00"}],
        },
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "insufficient_stock"


@pytest.mark.e2e
def test_venta_que_no_cuadra_devuelve_422(client: TestClient) -> None:
    producto = _create_product(client, stock="10")
    resp = client.post(
        "/sales",
        json={
            "lines": [{"product_id": producto["id"], "quantity": "2"}],
            "payments": [{"method": "cash", "amount": "150.00"}],
        },
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "payments_do_not_match_total"
