from __future__ import annotations

import flet as ft

from app.state.app_state import AppState
from app.views.balance_view import build_balance_view
from app.views.inventory_view import build_inventory_view
from app.views.sales_view import build_sales_view


def main(page: ft.Page) -> None:
    page.title = "indumentaria-pos"
    page.padding = 16
    state = AppState()

    page.add(
        ft.Tabs(
            length=3,
            selected_index=0,
            expand=True,
            content=ft.Column(
                [
                    ft.TabBar(
                        tabs=[
                            ft.Tab(label="Inventario", icon=ft.Icons.INVENTORY_2),
                            ft.Tab(label="Ventas", icon=ft.Icons.SHOPPING_CART),
                            ft.Tab(label="Balance", icon=ft.Icons.BAR_CHART),
                        ]
                    ),
                    ft.TabBarView(
                        expand=True,
                        controls=[
                            build_inventory_view(page, state.client),
                            build_sales_view(page, state.client),
                            build_balance_view(page, state.client),
                        ],
                    ),
                ],
                expand=True,
            ),
        )
    )


if __name__ == "__main__":
    ft.run(main)
