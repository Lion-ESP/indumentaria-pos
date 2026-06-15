from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, status

from app.inventory.entrypoints.schemas import (
    AdjustStockRequest,
    CreateProductRequest,
    ProductResponse,
)

router = APIRouter(prefix="/products", tags=["inventory"])

# FASE 1 — respuestas mockeadas y deterministas para desbloquear al frontend
# y validar el contrato. El wiring real con los casos de uso llega en Fase 3.
_MOCK_PRODUCT_ID = UUID("11111111-1111-1111-1111-111111111111")


def _mock_product(product_id: UUID) -> ProductResponse:
    return ProductResponse(
        id=product_id,
        sku="REM-001",
        name="Remera",
        unit="unit",
        cost_price=Decimal("60.00"),
        sale_price=Decimal("100.00"),
        stock=Decimal("10"),
        gross_margin_unit=Decimal("40.00"),
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
def create_product(body: CreateProductRequest) -> ProductResponse:
    return ProductResponse(
        id=uuid4(),
        sku=body.sku,
        name=body.name,
        unit=body.unit,
        cost_price=body.cost_price,
        sale_price=body.sale_price,
        stock=body.initial_stock,
        gross_margin_unit=body.sale_price - body.cost_price,
    )


@router.get("", response_model=list[ProductResponse])
def list_products() -> list[ProductResponse]:
    return [_mock_product(_MOCK_PRODUCT_ID)]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: UUID) -> ProductResponse:
    return _mock_product(product_id)


@router.post("/{product_id}/stock", response_model=ProductResponse)
def adjust_stock(product_id: UUID, body: AdjustStockRequest) -> ProductResponse:
    product = _mock_product(product_id)
    product.stock = product.stock + body.delta
    return product
