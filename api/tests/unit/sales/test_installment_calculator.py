from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.sales.domain.entities import Payment, PaymentMethod
from app.sales.domain.exceptions import CuotasInvalidasException
from app.sales.domain.services import InstallmentCalculator, add_months
from app.shared.domain.money import Money


@pytest.mark.unit
class TestInstallmentCalculator:
    def test_tres_cuotas_la_ultima_absorbe_el_redondeo(self) -> None:
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("100.00")), installments_count=3)
        cuotas = InstallmentCalculator().build(payment, date(2026, 1, 1))
        montos = [cuota.amount.amount for cuota in cuotas]
        assert montos == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        assert sum(montos) == Decimal("100.00")

    def test_aplica_recargo_financiero(self) -> None:
        payment = Payment(
            PaymentMethod.CREDIT_CARD,
            Money(Decimal("100.00")),
            installments_count=2,
            surcharge_rate=Decimal("0.20"),
        )
        cuotas = InstallmentCalculator().build(payment, date(2026, 1, 1))
        assert sum(cuota.amount.amount for cuota in cuotas) == Decimal("120.00")

    def test_vencimientos_mensuales_consecutivos(self) -> None:
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("90.00")), installments_count=3)
        cuotas = InstallmentCalculator().build(payment, date(2026, 1, 15))
        assert [cuota.due_date for cuota in cuotas] == [
            date(2026, 1, 15),
            date(2026, 2, 15),
            date(2026, 3, 15),
        ]

    def test_pago_no_tarjeta_no_genera_cuotas(self) -> None:
        payment = Payment(PaymentMethod.CASH, Money(Decimal("100.00")))
        assert InstallmentCalculator().build(payment, date(2026, 1, 1)) == []

    def test_cuotas_menor_a_uno_lanza(self) -> None:
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("100.00")), installments_count=0)
        with pytest.raises(CuotasInvalidasException):
            InstallmentCalculator().build(payment, date(2026, 1, 1))


@pytest.mark.unit
class TestAddMonths:
    def test_suma_meses_dentro_del_anio(self) -> None:
        assert add_months(date(2026, 1, 15), 2) == date(2026, 3, 15)

    def test_cruza_de_anio(self) -> None:
        assert add_months(date(2026, 11, 10), 3) == date(2027, 2, 10)

    def test_clampa_dia_al_ultimo_del_mes(self) -> None:
        assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
