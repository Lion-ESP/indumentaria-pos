from __future__ import annotations

import pytest

from app.inventory.domain.sku import format_auto_sku, parse_auto_sku


@pytest.mark.unit
class TestFormatAutoSku:
    def test_aplica_prefijo_y_padding(self) -> None:
        assert format_auto_sku(1) == "ART-0001"

    def test_no_recorta_correlativos_grandes(self) -> None:
        assert format_auto_sku(12345) == "ART-12345"


@pytest.mark.unit
class TestParseAutoSku:
    def test_recupera_el_correlativo(self) -> None:
        assert parse_auto_sku("ART-0007") == 7

    @pytest.mark.parametrize("foreign_sku", ["REM-001", "ART-X", "0001", "ART-"])
    def test_devuelve_none_para_sku_no_autogenerado(self, foreign_sku: str) -> None:
        assert parse_auto_sku(foreign_sku) is None
