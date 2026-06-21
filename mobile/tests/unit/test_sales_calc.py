from __future__ import annotations

from decimal import Decimal

import pytest

from app.views.sales_calc import change_due, line_total


@pytest.mark.unit
class TestLineTotal:
    def test_cantidad_entera(self) -> None:
        assert line_total(Decimal("100.00"), Decimal("2")) == Decimal("200.00")

    def test_cantidad_fraccionaria_redondea_half_up(self) -> None:
        assert line_total(Decimal("120.50"), Decimal("2.750")) == Decimal("331.38")


@pytest.mark.unit
class TestChangeDue:
    def test_recibido_mayor_devuelve_vuelto_positivo(self) -> None:
        assert change_due(Decimal("200.00"), Decimal("250.00")) == Decimal("50.00")

    def test_recibido_exacto_devuelve_cero(self) -> None:
        assert change_due(Decimal("200.00"), Decimal("200.00")) == Decimal("0.00")

    def test_recibido_menor_devuelve_faltante_negativo(self) -> None:
        assert change_due(Decimal("200.00"), Decimal("150.00")) == Decimal("-50.00")
