from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import flet as ft

from app.api_client import (
    ApiError,
    PaymentInput,
    PosApiClient,
    Product,
    SaleInput,
    SaleLineInput,
)
from app.views import validators as v
from app.views.sales_calc import change_due, line_total
from app.views.ui import notify, section_card


def build_sales_view(page: ft.Page, client: PosApiClient) -> ft.Control:
    product = ft.Dropdown(
        label="Producto",
        width=360,
        editable=True,
        enable_filter=True,
        enable_search=True,
    )
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
    received = ft.TextField(label="Efectivo recibido", width=160)
    empty_hint = ft.Text(color=ft.Colors.OUTLINE)
    total_info = ft.Text(weight=ft.FontWeight.BOLD)
    change_info = ft.Text(weight=ft.FontWeight.BOLD)
    catalog: dict[str, Product] = {}

    def selected_product() -> Product | None:
        return catalog.get(product.value or "")

    def current_total() -> Decimal | None:
        producto = selected_product()
        qty = v.parse_decimal(quantity.value)
        if producto is None or qty is None or qty <= 0:
            return None
        return line_total(producto.sale_price, qty)

    def recalc() -> None:
        producto = selected_product()
        total = current_total()
        if producto is None:
            total_info.value = ""
        elif total is None:
            total_info.value = f"Precio unitario ${producto.sale_price}"
        else:
            total_info.value = f"Precio unitario ${producto.sale_price}  ·  Total ${total}"

        recibido = v.parse_decimal(received.value)
        if total is None or recibido is None or not received.value.strip():
            change_info.value = ""
            return
        diferencia = change_due(total, recibido)
        if diferencia >= 0:
            change_info.value = f"Vuelto ${diferencia}"
            change_info.color = ft.Colors.GREEN
        else:
            change_info.value = f"Faltante ${-diferencia}"
            change_info.color = ft.Colors.RED

    def load_products() -> None:
        try:
            productos = client.list_products()
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
            return
        catalog.clear()
        catalog.update({str(p.id): p for p in productos})
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
        received.error = v.positive_decimal(received.value) if received.value.strip() else None
        return not (product.error_text or quantity.error or received.error)

    def on_change() -> None:
        validate()
        recalc()
        page.update()

    def on_refresh() -> None:
        load_products()
        recalc()
        page.update()

    def do_register(total: Decimal, recibido: Decimal | None) -> None:
        try:
            venta = client.register_sale(
                SaleInput(
                    lines=[
                        SaleLineInput(
                            product_id=UUID(product.value),
                            quantity=v.parse_decimal(quantity.value) or Decimal("0"),
                        )
                    ],
                    payments=[PaymentInput(method=method.value or "cash", amount=total)],
                )
            )
            mensaje = f"Venta registrada · total {venta.total}"
            if recibido is not None and recibido > total:
                mensaje += f" · vuelto ${change_due(total, recibido)}"
            notify(page, mensaje)
            quantity.value = "1"
            received.value = ""
            load_products()
            recalc()
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
        page.update()

    def confirm_faltante(total: Decimal, recibido: Decimal) -> None:
        def cancel() -> None:
            page.pop_dialog()

        def confirm() -> None:
            page.pop_dialog()
            do_register(total, recibido)

        faltante = -change_due(total, recibido)
        page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Efectivo insuficiente"),
                content=ft.Text(
                    f"El efectivo recibido (${recibido}) es menor al total (${total}); "
                    f"faltan ${faltante}. La venta se registra igual por el total. ¿Continuar?"
                ),
                actions=[
                    ft.TextButton("Cancelar", on_click=cancel),
                    ft.FilledButton("Registrar igual", on_click=confirm),
                ],
            )
        )

    def on_register() -> None:
        if not validate():
            page.update()
            return
        total = current_total()
        if total is None:
            page.update()
            return
        recibido = v.parse_decimal(received.value) if received.value.strip() else None
        if recibido is not None and recibido < total:
            confirm_faltante(total, recibido)
        else:
            do_register(total, recibido)

    for field in (quantity, received):
        field.on_change = on_change
    product.on_select = on_change

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
            ft.Row([quantity, method, received], wrap=True),
            total_info,
            change_info,
            ft.FilledButton("Registrar venta", icon=ft.Icons.POINT_OF_SALE, on_click=on_register),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
    )
    return section_card("Registrar venta", ft.Icons.SHOPPING_CART, body)
