from __future__ import annotations

import flet as ft

from app.state.app_state import AppState
from app.views.balance_view import build_balance_view
from app.views.inventory_view import build_inventory_view
from app.views.sales_view import build_sales_view


def main(page: ft.Page) -> None:
    page.title = "indumentaria-pos"
    page.scroll = ft.ScrollMode.AUTO
    state = AppState()

    page.add(
        build_inventory_view(page, state.client),
        ft.Divider(),
        build_sales_view(page, state.client),
        ft.Divider(),
        build_balance_view(page, state.client),
    )


if __name__ == "__main__":
    ft.run(main)
