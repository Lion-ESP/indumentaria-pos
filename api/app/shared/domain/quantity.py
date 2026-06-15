from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class UnitOfMeasure(StrEnum):
    UNIT = "unit"
    METER = "meter"
    KILOGRAM = "kg"

    @property
    def is_fractional(self) -> bool:
        """True si la unidad admite cantidades decimales (mercería)."""
        return self in (UnitOfMeasure.METER, UnitOfMeasure.KILOGRAM)


@dataclass(frozen=True, slots=True)
class Quantity:
    """Cantidad con su unidad de medida. Valida la fraccionabilidad según la
    unidad: METER/KG admiten decimales; UNIT solo enteros."""

    value: Decimal
    unit: UnitOfMeasure

    def __post_init__(self) -> None:
        value = Decimal(self.value)
        object.__setattr__(self, "value", value)
        if value < 0:
            raise ValueError("Quantity no puede ser negativa")
        if not self.unit.is_fractional and value != value.to_integral_value():
            raise ValueError(f"La unidad {self.unit.value} no admite cantidades fraccionadas")

    def add(self, other: Quantity) -> Quantity:
        self._assert_same_unit(other)
        return Quantity(self.value + other.value, self.unit)

    def subtract(self, other: Quantity) -> Quantity:
        self._assert_same_unit(other)
        return Quantity(self.value - other.value, self.unit)

    def is_enough_for(self, requested: Quantity) -> bool:
        self._assert_same_unit(requested)
        return self.value >= requested.value

    def _assert_same_unit(self, other: Quantity) -> None:
        if self.unit != other.unit:
            raise ValueError(f"Unidades incompatibles: {self.unit} vs {other.unit}")
