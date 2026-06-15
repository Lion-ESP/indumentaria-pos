from __future__ import annotations

from app.inventory.adapters.models import ProductModel
from app.inventory.domain.entities import Product
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure


def to_domain(row: ProductModel) -> Product:
    unit = UnitOfMeasure(row.unit)
    return Product(
        id=row.id,
        sku=row.sku,
        name=row.name,
        unit=unit,
        cost_price=Money(row.cost_price),
        sale_price=Money(row.sale_price),
        stock=Quantity(row.stock_value, unit),
        photo_path=row.photo_path,
        active=row.active,
    )


def to_model(product: Product) -> ProductModel:
    return ProductModel(
        id=product.id,
        sku=product.sku,
        name=product.name,
        unit=product.unit.value,
        cost_price=product.cost_price.amount,
        sale_price=product.sale_price.amount,
        stock_value=product.current_stock.value,
        photo_path=product.photo_path,
        active=product.active,
    )
