from __future__ import annotations

from decimal import Decimal

import pytest

from app.views import validators as v


@pytest.mark.unit
class TestParseDecimal:
    def test_parsea_numero_valido(self) -> None:
        assert v.parse_decimal(" 12.50 ") == Decimal("12.50")

    @pytest.mark.parametrize("not_a_number", ["", None, "abc", "1,5"])
    def test_devuelve_none_ante_valor_invalido(self, not_a_number: str | None) -> None:
        assert v.parse_decimal(not_a_number) is None


@pytest.mark.unit
class TestRequired:
    @pytest.mark.parametrize("empty_value", ["", "   ", None])
    def test_campo_vacio_devuelve_error(self, empty_value: str | None) -> None:
        assert v.required(empty_value) is not None

    def test_campo_con_contenido_es_valido(self) -> None:
        assert v.required("REM-001") is None


@pytest.mark.unit
class TestPositiveDecimal:
    def test_mayor_a_cero_es_valido(self) -> None:
        assert v.positive_decimal("0.01") is None

    @pytest.mark.parametrize("non_positive", ["0", "-5"])
    def test_cero_o_negativo_devuelve_error(self, non_positive: str) -> None:
        assert v.positive_decimal(non_positive) is not None

    def test_no_numerico_devuelve_error(self) -> None:
        assert v.positive_decimal("x") is not None


@pytest.mark.unit
class TestNonNegativeDecimal:
    @pytest.mark.parametrize("non_negative", ["0", "3.5"])
    def test_cero_o_positivo_es_valido(self, non_negative: str) -> None:
        assert v.non_negative_decimal(non_negative) is None

    def test_negativo_devuelve_error(self) -> None:
        assert v.non_negative_decimal("-0.1") is not None


@pytest.mark.unit
class TestSaleAboveCost:
    def test_venta_mayor_a_costo_es_valido(self) -> None:
        assert v.sale_above_cost("60.00", "100.00") is None

    @pytest.mark.parametrize(("cost", "sale"), [("100", "100"), ("100", "80")])
    def test_venta_menor_o_igual_a_costo_devuelve_error(self, cost: str, sale: str) -> None:
        assert v.sale_above_cost(cost, sale) is not None

    def test_si_algun_campo_no_es_numerico_no_evalua_la_regla(self) -> None:
        assert v.sale_above_cost("", "100") is None


@pytest.mark.unit
class TestIsoDate:
    def test_fecha_iso_valida(self) -> None:
        assert v.iso_date("2026-06-20") is None

    @pytest.mark.parametrize("malformed", ["20-06-2026", "2026/06/20", "", None])
    def test_formato_invalido_devuelve_error(self, malformed: str | None) -> None:
        assert v.iso_date(malformed) is not None


@pytest.mark.unit
class TestDateRange:
    def test_desde_anterior_a_hasta_es_valido(self) -> None:
        assert v.date_range("2026-01-01", "2026-12-31") is None

    def test_desde_posterior_a_hasta_devuelve_error(self) -> None:
        assert v.date_range("2026-12-31", "2026-01-01") is not None

    def test_no_evalua_rango_si_una_fecha_es_invalida(self) -> None:
        assert v.date_range("malformada", "2026-01-01") is None
