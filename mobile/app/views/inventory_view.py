from __future__ import annotations

from decimal import Decimal

import flet as ft

from app.api_client import ApiError, PosApiClient, ProductInput
from app.views import validators as v
from app.views.ui import notify, section_card


def build_inventory_view(page: ft.Page, client: PosApiClient) -> ft.Control:
    sku = ft.TextField(label="SKU", width=200)
    name = ft.TextField(label="Nombre", width=240)
    unit = ft.Dropdown(
        label="Unidad",
        value="unit",
        width=140,
        options=[
            ft.dropdown.Option("unit"),
            ft.dropdown.Option("meter"),
            ft.dropdown.Option("kg"),
        ],
    )
    cost_price = ft.TextField(label="Precio costo", width=140)
    sale_price = ft.TextField(label="Precio venta", width=140)
    initial_stock = ft.TextField(label="Stock inicial", value="0", width=140)
    empty_hint = ft.Text(color=ft.Colors.OUTLINE)
    listado = ft.Column(spacing=4)

    def validate() -> bool:
        sku.error = v.required(sku.value)
        name.error = v.required(name.value)
        cost_price.error = v.positive_decimal(cost_price.value)
        sale_price.error = v.positive_decimal(sale_price.value) or v.sale_above_cost(
            cost_price.value, sale_price.value
        )
        initial_stock.error = v.non_negative_decimal(initial_stock.value)
        return not any(field.error for field in (sku, name, cost_price, sale_price, initial_stock))

    def refresh() -> None:
        try:
            productos = client.list_products()
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
            return
        listado.controls = [
            ft.Text(f"{p.sku} · {p.name} · stock {p.stock} {p.unit} · margen {p.gross_margin_unit}")
            for p in productos
        ]
        empty_hint.value = "" if productos else "Todavía no hay productos cargados."

    def on_change() -> None:
        validate()
        page.update()

    def on_create() -> None:
        if not validate():
            page.update()
            return
        try:
            producto = client.create_product(
                ProductInput(
                    sku=sku.value or "",
                    name=name.value or "",
                    unit=unit.value or "unit",
                    cost_price=v.parse_decimal(cost_price.value) or Decimal("0"),
                    sale_price=v.parse_decimal(sale_price.value) or Decimal("0"),
                    initial_stock=v.parse_decimal(initial_stock.value) or Decimal("0"),
                )
            )
            notify(page, f"Producto creado: {producto.sku}")
            for field in (sku, name, cost_price, sale_price):
                field.value = ""
            initial_stock.value = "0"
            refresh()
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
        page.update()

    for field in (sku, name, cost_price, sale_price, initial_stock):
        field.on_change = on_change

    refresh()
    body = ft.Column(
        [
            ft.Row([sku, name, unit], wrap=True),
            ft.Row([cost_price, sale_price, initial_stock], wrap=True),
            ft.FilledButton("Crear producto", icon=ft.Icons.ADD, on_click=on_create),
            ft.Divider(),
            ft.Text("Productos", weight=ft.FontWeight.BOLD),
            empty_hint,
            listado,
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
    )
    return section_card("Inventario", ft.Icons.INVENTORY_2, body)
