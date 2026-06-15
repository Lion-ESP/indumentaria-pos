from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

CENTS = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class Money:
    """Valor monetario inmutable. Internamente SIEMPRE Decimal, cuantizado a
    centavos con redondeo half-up. Nunca usar float para dinero."""

    amount: Decimal

    def __post_init__(self) -> None:
        quantized = Decimal(self.amount).quantize(CENTS, rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", quantized)

    @classmethod
    def zero(cls) -> Money:
        return cls(Decimal("0"))

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        return Money(self.amount - other.amount)

    def multiply(self, factor: Decimal | int) -> Money:
        return Money(self.amount * Decimal(factor))

    def is_negative(self) -> bool:
        return self.amount < 0
