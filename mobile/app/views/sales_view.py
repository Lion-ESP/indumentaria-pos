from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import flet as ft

from app.api_client import ApiError, PaymentInput, PosApiClient, SaleInput, SaleLineInput
from app.views import validators as v
from app.views.ui import notify, section_card


def build_sales_view(page: ft.Page, client: PosApiClient) -> ft.Control:
    product = ft.Dropdown(label="Producto", width=360)
    quantity = ft.TextField(label="Cantidad", value="1", width=120)
    method = ft.Dropdown(
        label="Medio de pago",
        value="cash",
        width=160,
        options=[
            ft.dropdown.Option("cash"),
            ft.dropdown.Option("debit"),
            ft.dropdown.Option("credit_card"),
            ft.dropdown.Option("transfer"),
        ],
    )
    amount = ft.TextField(label="Monto pagado", width=140)
    empty_hint = ft.Text(color=ft.Colors.OUTLINE)

    def load_products() -> None:
        try:
            productos = client.list_products()
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
            return
        product.options = [
            ft.dropdown.Option(
                key=str(p.id),
                text=f"{p.sku} · {p.name} · stock {p.stock} {p.unit}",
            )
            for p in productos
        ]
        empty_hint.value = "" if productos else "No hay productos cargados. Creá uno en Inventario."

    def validate() -> bool:
        product.error_text = None if product.value else "Seleccioná un producto."
        quantity.error = v.positive_decimal(quantity.value)
        amount.error = v.positive_decimal(amount.value)
        return not (product.error_text or quantity.error or amount.error)

    def on_change() -> None:
        validate()
        page.update()

    def on_refresh() -> None:
        load_products()
        page.update()

    def on_register() -> None:
        if not validate():
            page.update()
            return
        try:
            venta = client.register_sale(
                SaleInput(
                    lines=[
                        SaleLineInput(
                            product_id=UUID(product.value),
                            quantity=v.parse_decimal(quantity.value) or Decimal("0"),
                        )
                    ],
                    payments=[
                        PaymentInput(
                            method=method.value or "cash",
                            amount=v.parse_decimal(amount.value) or Decimal("0"),
                        )
                    ],
                )
            )
            notify(page, f"Venta registrada · total {venta.total} · ganancia {venta.gross_profit}")
            load_products()
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
        page.update()

    for field in (quantity, amount):
        field.on_change = on_change

    load_products()
    body = ft.Column(
        [
            ft.Row(
                [
                    product,
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, tooltip="Actualizar productos", on_click=on_refresh
                    ),
                ]
            ),
            empty_hint,
            ft.Row([quantity, method, amount], wrap=True),
            ft.FilledButton("Registrar venta", icon=ft.Icons.POINT_OF_SALE, on_click=on_register),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
    )
    return section_card("Registrar venta", ft.Icons.SHOPPING_CART, body)
