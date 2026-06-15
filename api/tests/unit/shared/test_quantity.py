from __future__ import annotations

from decimal import Decimal

import pytest

from app.shared.domain.quantity import Quantity, UnitOfMeasure


@pytest.mark.unit
class TestUnitOfMeasure:
    def test_unit_no_es_fraccional(self) -> None:
        assert not UnitOfMeasure.UNIT.is_fractional

    def test_meter_y_kg_son_fraccionales(self) -> None:
        assert UnitOfMeasure.METER.is_fractional
        assert UnitOfMeasure.KILOGRAM.is_fractional


@pytest.mark.unit
class TestQuantity:
    def test_metro_admite_fraccion(self) -> None:
        cantidad = Quantity(Decimal("2.750"), UnitOfMeasure.METER)
        assert cantidad.value == Decimal("2.750")

    def test_unidad_discreta_rechaza_fraccion(self) -> None:
        with pytest.raises(ValueError, match="no admite cantidades fraccionadas"):
            Quantity(Decimal("2.5"), UnitOfMeasure.UNIT)

    def test_no_admite_negativa(self) -> None:
        with pytest.raises(ValueError, match="no puede ser negativa"):
            Quantity(Decimal("-1"), UnitOfMeasure.METER)

    def test_add(self) -> None:
        resultado = Quantity(Decimal("1.5"), UnitOfMeasure.METER).add(
            Quantity(Decimal("2.0"), UnitOfMeasure.METER)
        )
        assert resultado.value == Decimal("3.5")

    def test_subtract(self) -> None:
        resultado = Quantity(Decimal("5"), UnitOfMeasure.UNIT).subtract(
            Quantity(Decimal("2"), UnitOfMeasure.UNIT)
        )
        assert resultado.value == Decimal("3")

    def test_is_enough_for(self) -> None:
        disponible = Quantity(Decimal("3"), UnitOfMeasure.UNIT)
        assert disponible.is_enough_for(Quantity(Decimal("3"), UnitOfMeasure.UNIT))
        assert not disponible.is_enough_for(Quantity(Decimal("4"), UnitOfMeasure.UNIT))

    def test_operacion_entre_unidades_incompatibles_falla(self) -> None:
        with pytest.raises(ValueError, match="Unidades incompatibles"):
            Quantity(Decimal("1"), UnitOfMeasure.METER).add(
                Quantity(Decimal("1"), UnitOfMeasure.KILOGRAM)
            )
