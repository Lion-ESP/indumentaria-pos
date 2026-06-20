"""Helpers de presentación compartidos por las vistas Flet.

Centralizan el feedback transitorio (SnackBar) y el contenedor visual de cada
sección, para que inventario, ventas y balance compartan look & feel sin
duplicar el armado del layout.
"""

from __future__ import annotations

import flet as ft


def notify(page: ft.Page, message: str, *, error: bool = False) -> None:
    """Muestra un SnackBar transitorio: verde para éxito, rojo para error."""
    page.show_dialog(
        ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_400 if error else ft.Colors.GREEN_600,
        )
    )


def section_card(title: str, icon: ft.IconData, body: ft.Control) -> ft.Control:
    """Envuelve el cuerpo de una vista en una tarjeta con encabezado e ícono."""
    return ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(icon, color=ft.Colors.PRIMARY),
                            ft.Text(title, size=20, weight=ft.FontWeight.BOLD),
                        ],
                        spacing=10,
                    ),
                    ft.Divider(height=1),
                    body,
                ],
                spacing=16,
            ),
        ),
    )
