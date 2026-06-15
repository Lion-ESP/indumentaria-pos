from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

import flet as ft

from app.api_client import ApiError, PaymentInput, PosApiClient, SaleInput, SaleLineInput


def build_sales_view(page: ft.Page, client: PosApiClient) -> ft.Control:
    product_id = ft.TextField(label="ID de producto", width=320)
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

    def on_register() -> None:
        try:
            venta = client.register_sale(
                SaleInput(
                    lines=[
                        SaleLineInput(
                            product_id=UUID(product_id.value or ""),
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
        except (InvalidOperation, ValueError):
            status.value = "Revisá el ID del producto, la cantidad y el monto."
        except ApiError as error:
            status.value = error.friendly_message
        page.update()

    return ft.Column(
        [
            ft.Text("Registrar venta", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([product_id, quantity], wrap=True),
            ft.Row([method, amount], wrap=True),
            ft.FilledButton("Registrar venta", on_click=on_register),
            status,
        ],
        scroll=ft.ScrollMode.AUTO,
    )
