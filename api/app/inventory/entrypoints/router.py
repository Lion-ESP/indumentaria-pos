from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.inventory.adapters.repositories import SqlProductRepository
from app.inventory.application.commands import AdjustStockCommand, CreateProductCommand
from app.inventory.application.use_cases import AdjustStockUseCase, CreateProductUseCase
from app.inventory.domain.entities import Product
from app.inventory.domain.exceptions import ProductNotFound
from app.inventory.entrypoints.dependencies import (
    get_adjust_stock_use_case,
    get_create_product_use_case,
    get_product_repository,
)
from app.inventory.entrypoints.schemas import (
    AdjustStockRequest,
    CreateProductRequest,
    ProductResponse,
)
from app.shared.domain.quantity import UnitOfMeasure

router = APIRouter(prefix="/products", tags=["inventory"])


def _to_response(product: Product) -> ProductResponse:
    return ProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        unit=product.unit.value,
        cost_price=product.cost_price.amount,
        sale_price=product.sale_price.amount,
        stock=product.current_stock.value,
        gross_margin_unit=product.gross_margin_unit.amount,
    )


def _require(repository: SqlProductRepository, product_id: UUID) -> Product:
    product = repository.get(product_id)
    if product is None:
        raise ProductNotFound(f"Producto {product_id} no encontrado")
    return product


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProductResponse)
def create_product(
    body: CreateProductRequest,
    use_case: CreateProductUseCase = Depends(get_create_product_use_case),
    repository: SqlProductRepository = Depends(get_product_repository),
) -> ProductResponse:
    product_id = use_case.execute(
        CreateProductCommand(
            sku=body.sku,
            name=body.name,
            unit=UnitOfMeasure(body.unit),
            cost_price=body.cost_price,
            sale_price=body.sale_price,
            initial_stock=body.initial_stock,
        )
    )
    return _to_response(_require(repository, product_id))


@router.get("", response_model=list[ProductResponse])
def list_products(
    repository: SqlProductRepository = Depends(get_product_repository),
) -> list[ProductResponse]:
    return [_to_response(product) for product in repository.list_active()]


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: UUID,
    repository: SqlProductRepository = Depends(get_product_repository),
) -> ProductResponse:
    return _to_response(_require(repository, product_id))


@router.post("/{product_id}/stock", response_model=ProductResponse)
def adjust_stock(
    product_id: UUID,
    body: AdjustStockRequest,
    use_case: AdjustStockUseCase = Depends(get_adjust_stock_use_case),
    repository: SqlProductRepository = Depends(get_product_repository),
) -> ProductResponse:
    use_case.execute(AdjustStockCommand(product_id=product_id, delta=body.delta))
    return _to_response(_require(repository, product_id))
