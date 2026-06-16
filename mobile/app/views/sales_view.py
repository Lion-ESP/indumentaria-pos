from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

import flet as ft

from app.api_client import ApiError, PaymentInput, PosApiClient, SaleInput, SaleLineInput


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
    status = ft.Text()

    def load_products() -> None:
        try:
            productos = client.list_products()
        except ApiError as error:
            status.value = error.friendly_message
            return
        product.options = [
            ft.dropdown.Option(
                key=str(p.id),
                text=f"{p.sku} · {p.name} · stock {p.stock} {p.unit}",
            )
            for p in productos
        ]
        if not productos:
            status.value = "No hay productos cargados. Creá uno en Inventario."

    def on_refresh() -> None:
        load_products()
        page.update()

    def on_register() -> None:
        selected = product.value
        if not selected:
            status.value = "Seleccioná un producto."
            page.update()
            return
        try:
            venta = client.register_sale(
                SaleInput(
                    lines=[
                        SaleLineInput(
                            product_id=UUID(selected),
                            quantity=Decimal(quantity.value or "0"),
                        )
                    ],
                    payments=[
                        PaymentInput(
                            method=method.value or "cash",
                            amount=Decimal(amount.value or "0"),
                        )
                    ],
                )
            )
            status.value = f"Venta registrada · total {venta.total} · ganancia {venta.gross_profit}"
            load_products()
        except (InvalidOperation, ValueError):
            status.value = "La cantidad y el monto deben ser numéricos."
        except ApiError as error:
            status.value = error.friendly_message
        page.update()

    load_products()
    return ft.Column(
        [
            ft.Text("Registrar venta", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([product, ft.IconButton(icon=ft.Icons.REFRESH, on_click=on_refresh)]),
            ft.Row([quantity, method, amount], wrap=True),
            ft.FilledButton("Registrar venta", on_click=on_register),
            status,
        ],
        scroll=ft.ScrollMode.AUTO,
    )
