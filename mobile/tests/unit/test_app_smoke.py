from __future__ import annotations

import importlib
from unittest.mock import MagicMock

import flet as ft
import pytest

from app.views.balance_view import build_balance_view
from app.views.inventory_view import build_inventory_view
from app.views.sales_view import build_sales_view


@pytest.mark.unit
def test_las_vistas_se_construyen_contra_la_api_de_flet() -> None:
    page = MagicMock()
    client = MagicMock()
    client.list_products.return_value = []

    assert isinstance(build_inventory_view(page, client), ft.Control)
    assert isinstance(build_sales_view(page, client), ft.Control)
    assert isinstance(build_balance_view(page, client), ft.Control)


@pytest.mark.unit
def test_el_modulo_main_importa() -> None:
    assert importlib.import_module("app.main") is not None
