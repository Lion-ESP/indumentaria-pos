from __future__ import annotations

from datetime import date

import flet as ft

from app.api_client import ApiError, PosApiClient
from app.views import validators as v
from app.views.ui import notify, section_card


def build_balance_view(page: ft.Page, client: PosApiClient) -> ft.Control:
    from_date = ft.TextField(label="Desde (YYYY-MM-DD)", value="2020-01-01", width=200)
    to_date = ft.TextField(label="Hasta (YYYY-MM-DD)", value="2099-12-31", width=200)
    resumen = ft.Text(weight=ft.FontWeight.BOLD)
    detalle = ft.Column(spacing=4)

    def validate() -> bool:
        from_date.error = v.iso_date(from_date.value)
        to_date.error = v.iso_date(to_date.value) or v.date_range(from_date.value, to_date.value)
        return not (from_date.error or to_date.error)

    def on_change() -> None:
        validate()
        page.update()

    def on_query() -> None:
        if not validate():
            page.update()
            return
        try:
            balance = client.get_balance(
                date.fromisoformat((from_date.value or "").strip()),
                date.fromisoformat((to_date.value or "").strip()),
            )
            resumen.value = (
                f"Ganancia bruta {balance.total_gross_profit} · neta {balance.total_net_profit}"
            )
            detalle.controls = [
                ft.Text(f"{b.period}: bruta {b.gross_profit} · neta {b.net_profit}")
                for b in balance.buckets
            ]
        except ApiError as error:
            notify(page, error.friendly_message, error=True)
        page.update()

    for field in (from_date, to_date):
        field.on_change = on_change

    body = ft.Column(
        [
            ft.Row([from_date, to_date], wrap=True),
            ft.FilledButton("Consultar balance", icon=ft.Icons.QUERY_STATS, on_click=on_query),
            ft.Divider(),
            resumen,
            detalle,
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
    )
    return section_card("Balance", ft.Icons.BAR_CHART, body)
