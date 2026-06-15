from __future__ import annotations

from datetime import date

import flet as ft

from app.api_client import ApiError, PosApiClient


def _parse_date(value: str | None, fallback: date) -> date:
    if not value:
        return fallback
    return date.fromisoformat(value)


def build_balance_view(page: ft.Page, client: PosApiClient) -> ft.Control:
    from_date = ft.TextField(label="Desde (YYYY-MM-DD)", value="2020-01-01", width=200)
    to_date = ft.TextField(label="Hasta (YYYY-MM-DD)", value="2099-12-31", width=200)
    status = ft.Text()
    resumen = ft.Text(weight=ft.FontWeight.BOLD)
    detalle = ft.Column()

    def on_query() -> None:
        try:
            balance = client.get_balance(
                _parse_date(from_date.value, date(2020, 1, 1)),
                _parse_date(to_date.value, date(2099, 12, 31)),
            )
            resumen.value = (
                f"Ganancia bruta {balance.total_gross_profit} · neta {balance.total_net_profit}"
            )
            detalle.controls = [
                ft.Text(f"{b.period}: bruta {b.gross_profit} · neta {b.net_profit}")
                for b in balance.buckets
            ]
            status.value = ""
        except ValueError:
            status.value = "Las fechas deben tener formato YYYY-MM-DD."
        except ApiError as error:
            status.value = error.friendly_message
        page.update()

    return ft.Column(
        [
            ft.Text("Balance", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([from_date, to_date], wrap=True),
            ft.FilledButton("Consultar balance", on_click=on_query),
            status,
            resumen,
            detalle,
        ],
        scroll=ft.ScrollMode.AUTO,
    )
