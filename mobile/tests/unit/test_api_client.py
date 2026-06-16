from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
import respx

from app.api_client import (
    ApiError,
    PaymentInput,
    PosApiClient,
    ProductInput,
    SaleInput,
    SaleLineInput,
)

BASE_URL = "http://api.test"


def _client() -> PosApiClient:
    return PosApiClient(BASE_URL, client=httpx.Client(base_url=BASE_URL))


@pytest.mark.unit
@respx.mock
def test_create_product_serializa_y_parsea() -> None:
    route = respx.post(f"{BASE_URL}/products").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": str(uuid4()),
                "sku": "REM-001",
                "name": "Remera",
                "unit": "unit",
                "cost_price": "60.00",
                "sale_price": "100.00",
                "stock": "10",
                "gross_margin_unit": "40.00",
            },
        )
    )

    with _client() as client:
        producto = client.create_product(
            ProductInput("REM-001", "Remera", "unit", Decimal("60"), Decimal("100"), Decimal("10"))
        )

    enviado = route.calls.last.request
    assert b'"cost_price":"60"' in enviado.content
    assert producto.gross_margin_unit == Decimal("40.00")
    assert producto.stock == Decimal("10")


@pytest.mark.unit
@respx.mock
def test_register_sale_devuelve_totales_en_decimal() -> None:
    respx.post(f"{BASE_URL}/sales").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": str(uuid4()),
                "total": "200.00",
                "total_paid": "200.00",
                "gross_profit": "80.00",
            },
        )
    )

    with _client() as client:
        venta = client.register_sale(
            SaleInput(
                lines=[SaleLineInput(uuid4(), Decimal("2"))],
                payments=[PaymentInput("cash", Decimal("200.00"))],
            )
        )

    assert venta.total == Decimal("200.00")
    assert venta.gross_profit == Decimal("80.00")


@pytest.mark.unit
@respx.mock
def test_stock_insuficiente_se_traduce_a_apierror() -> None:
    respx.post(f"{BASE_URL}/sales").mock(
        return_value=httpx.Response(
            409,
            json={"error": {"code": "insufficient_stock", "message": "no alcanza"}},
        )
    )

    with _client() as client, pytest.raises(ApiError) as exc_info:
        client.register_sale(
            SaleInput(
                lines=[SaleLineInput(uuid4(), Decimal("5"))],
                payments=[PaymentInput("cash", Decimal("500"))],
            )
        )

    assert exc_info.value.code == "insufficient_stock"
    assert exc_info.value.status_code == 409
    assert "stock" in exc_info.value.friendly_message.lower()


@pytest.mark.unit
@respx.mock
def test_validacion_de_fastapi_se_traduce_a_apierror() -> None:
    respx.post(f"{BASE_URL}/products").mock(
        return_value=httpx.Response(422, json={"detail": [{"loc": ["body", "unit"]}]})
    )

    with _client() as client, pytest.raises(ApiError) as exc_info:
        client.create_product(ProductInput("X", "X", "litros", Decimal("1"), Decimal("2")))

    assert exc_info.value.code == "validation_error"
    assert exc_info.value.status_code == 422


@pytest.mark.unit
@respx.mock
def test_list_y_get_product() -> None:
    product_id = uuid4()
    payload = {
        "id": str(product_id),
        "sku": "REM-001",
        "name": "Remera",
        "unit": "unit",
        "cost_price": "60.00",
        "sale_price": "100.00",
        "stock": "8",
        "gross_margin_unit": "40.00",
    }
    respx.get(f"{BASE_URL}/products").mock(return_value=httpx.Response(200, json=[payload]))
    respx.get(f"{BASE_URL}/products/{product_id}").mock(
        return_value=httpx.Response(200, json=payload)
    )

    with _client() as client:
        listado = client.list_products()
        detalle = client.get_product(product_id)

    assert listado[0].id == product_id
    assert detalle.stock == Decimal("8")


@pytest.mark.unit
@respx.mock
def test_get_balance_agrega_buckets() -> None:
    respx.get(f"{BASE_URL}/reports/balance").mock(
        return_value=httpx.Response(
            200,
            json={
                "from_date": "2026-01-01",
                "to_date": "2026-12-31",
                "group_by": "day",
                "total_gross_profit": "80.00",
                "total_net_profit": "80.00",
                "buckets": [
                    {"period": "2026-06-15", "gross_profit": "80.00", "net_profit": "80.00"}
                ],
            },
        )
    )

    with _client() as client:
        balance = client.get_balance(date(2026, 1, 1), date(2026, 12, 31))

    assert balance.total_gross_profit == Decimal("80.00")
    assert balance.buckets[0].period == "2026-06-15"


@pytest.mark.unit
@respx.mock
def test_adjust_stock() -> None:
    product_id = uuid4()
    respx.post(f"{BASE_URL}/products/{product_id}/stock").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": str(product_id),
                "sku": "REM-001",
                "name": "Remera",
                "unit": "unit",
                "cost_price": "60.00",
                "sale_price": "100.00",
                "stock": "15",
                "gross_margin_unit": "40.00",
            },
        )
    )

    with _client() as client:
        producto = client.adjust_stock(product_id, Decimal("5"))

    assert producto.stock == Decimal("15")


@pytest.mark.unit
@respx.mock
def test_respuesta_de_error_sin_json_se_traduce() -> None:
    respx.get(f"{BASE_URL}/products").mock(
        return_value=httpx.Response(503, text="Service Unavailable")
    )

    with _client() as client, pytest.raises(ApiError) as exc_info:
        client.list_products()

    assert exc_info.value.code == "http_error"
    assert exc_info.value.status_code == 503


@pytest.mark.unit
@respx.mock
def test_error_con_payload_desconocido_se_traduce() -> None:
    respx.get(f"{BASE_URL}/products").mock(return_value=httpx.Response(400, json={"foo": "bar"}))

    with _client() as client, pytest.raises(ApiError) as exc_info:
        client.list_products()

    assert exc_info.value.code == "http_error"
    assert exc_info.value.status_code == 400
