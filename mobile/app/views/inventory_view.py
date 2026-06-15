from __future__ import annotations

from decimal import Decimal, InvalidOperation

import flet as ft

from app.api_client import ApiError, PosApiClient, ProductInput


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
    status = ft.Text()
    listado = ft.Column()

    def refresh() -> None:
        try:
            productos = client.list_products()
        except ApiError as error:
            status.value = error.friendly_message
            return
        listado.controls = [
            ft.Text(f"{p.sku} · {p.name} · stock {p.stock} {p.unit} · margen {p.gross_margin_unit}")
            for p in productos
        ]

    def on_create() -> None:
        try:
            producto = client.create_product(
                ProductInput(
                    sku=sku.value or "",
                    name=name.value or "",
                    unit=unit.value or "unit",
                    cost_price=Decimal(cost_price.value or "0"),
                    sale_price=Decimal(sale_price.value or "0"),
                    initial_stock=Decimal(initial_stock.value or "0"),
                )
            )
            status.value = f"Producto creado: {producto.sku}"
            refresh()
        except InvalidOperation:
            status.value = "Los precios y el stock deben ser numéricos."
        except ApiError as error:
            status.value = error.friendly_message
        page.update()

    refresh()
    return ft.Column(
        [
            ft.Text("Inventario", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([sku, name, unit], wrap=True),
            ft.Row([cost_price, sale_price, initial_stock], wrap=True),
            ft.FilledButton("Crear producto", on_click=on_create),
            status,
            ft.Divider(),
            ft.Text("Productos", weight=ft.FontWeight.BOLD),
            listado,
        ],
        scroll=ft.ScrollMode.AUTO,
    )
