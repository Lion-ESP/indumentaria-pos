from __future__ import annotations

from decimal import Decimal

import pytest

from app.shared.domain.money import Money


@pytest.mark.unit
class TestMoney:
    def test_cuantiza_a_dos_decimales_half_up(self) -> None:
        assert Money(Decimal("10.005")).amount == Decimal("10.01")

    def test_zero(self) -> None:
        assert Money.zero().amount == Decimal("0.00")

    def test_suma(self) -> None:
        assert (Money(Decimal("10.00")) + Money(Decimal("5.50"))).amount == Decimal("15.50")

    def test_resta(self) -> None:
        assert (Money(Decimal("10.00")) - Money(Decimal("3.30"))).amount == Decimal("6.70")

    def test_multiply_por_cantidad(self) -> None:
        assert Money(Decimal("100.00")).multiply(Decimal("2.75")).amount == Decimal("275.00")

    def test_is_negative(self) -> None:
        assert Money(Decimal("-1.00")).is_negative()
        assert not Money(Decimal("1.00")).is_negative()

    def test_es_inmutable(self) -> None:
        money = Money(Decimal("1.00"))
        with pytest.raises(AttributeError):
            money.amount = Decimal("2.00")  # type: ignore[misc]
