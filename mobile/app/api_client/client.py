from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx

from app.api_client.errors import raise_for_domain_error
from app.api_client.models import (
    Balance,
    BalanceBucket,
    Product,
    ProductInput,
    Sale,
    SaleInput,
)


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def _to_product(data: dict[str, Any]) -> Product:
    return Product(
        id=UUID(data["id"]),
        sku=data["sku"],
        name=data["name"],
        unit=data["unit"],
        cost_price=_dec(data["cost_price"]),
        sale_price=_dec(data["sale_price"]),
        stock=_dec(data["stock"]),
        gross_margin_unit=_dec(data["gross_margin_unit"]),
    )


def _to_sale(data: dict[str, Any]) -> Sale:
    return Sale(
        id=UUID(data["id"]),
        total=_dec(data["total"]),
        total_paid=_dec(data["total_paid"]),
        gross_profit=_dec(data["gross_profit"]),
    )


class PosApiClient:
    """Cliente HTTP tipado contra /api. Encapsula la serialización de DTOs y la
    traducción de errores de negocio a ApiError (por `code`)."""

    def __init__(self, base_url: str, *, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=10.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PosApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        response = self._client.request(method, url, **kwargs)
        raise_for_domain_error(response)
        return response.json()

    def create_product(self, data: ProductInput) -> Product:
        body = {
            "sku": data.sku,
            "name": data.name,
            "unit": data.unit,
            "cost_price": str(data.cost_price),
            "sale_price": str(data.sale_price),
            "initial_stock": str(data.initial_stock),
        }
        return _to_product(self._request("POST", "/products", json=body))

    def list_products(self) -> list[Product]:
        return [_to_product(item) for item in self._request("GET", "/products")]

    def get_product(self, product_id: UUID) -> Product:
        return _to_product(self._request("GET", f"/products/{product_id}"))

    def adjust_stock(self, product_id: UUID, delta: Decimal) -> Product:
        body = {"delta": str(delta)}
        return _to_product(self._request("POST", f"/products/{product_id}/stock", json=body))

    def register_sale(self, data: SaleInput) -> Sale:
        body = {
            "lines": [
                {"product_id": str(line.product_id), "quantity": str(line.quantity)}
                for line in data.lines
            ],
            "payments": [
                {
                    "method": payment.method,
                    "amount": str(payment.amount),
                    "installments_count": payment.installments_count,
                    "surcharge_rate": str(payment.surcharge_rate),
                }
                for payment in data.payments
            ],
        }
        return _to_sale(self._request("POST", "/sales", json=body))

    def get_balance(self, from_date: date, to_date: date, group_by: str = "day") -> Balance:
        params = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "group_by": group_by,
        }
        data = self._request("GET", "/reports/balance", params=params)
        return Balance(
            total_gross_profit=_dec(data["total_gross_profit"]),
            total_net_profit=_dec(data["total_net_profit"]),
            buckets=[
                BalanceBucket(
                    period=bucket["period"],
                    gross_profit=_dec(bucket["gross_profit"]),
                    net_profit=_dec(bucket["net_profit"]),
                )
                for bucket in data["buckets"]
            ],
        )
