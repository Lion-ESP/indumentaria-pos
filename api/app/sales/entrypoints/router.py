from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.sales.adapters.repositories import SqlSaleRepository
from app.sales.application.commands import (
    LineCommand,
    PaymentCommand,
    RegisterSaleCommand,
)
from app.sales.application.use_cases import RegisterSaleUseCase
from app.sales.entrypoints.dependencies import (
    get_register_sale_use_case,
    get_sale_repository,
)
from app.sales.entrypoints.schemas import RegisterSaleRequest, SaleResponse

router = APIRouter(prefix="/sales", tags=["sales"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
def register_sale(
    body: RegisterSaleRequest,
    use_case: RegisterSaleUseCase = Depends(get_register_sale_use_case),
    repository: SqlSaleRepository = Depends(get_sale_repository),
) -> SaleResponse:
    command = RegisterSaleCommand(
        lines=[LineCommand(line.product_id, line.quantity) for line in body.lines],
        payments=[
            PaymentCommand(
                payment.method,
                payment.amount,
                payment.installments_count,
                payment.surcharge_rate,
            )
            for payment in body.payments
        ],
    )
    sale_id = use_case.execute(command)
    sale = repository.get(sale_id)
    assert sale is not None
    return SaleResponse(
        id=sale.id,
        total=sale.total.amount,
        total_paid=sale.total_paid.amount,
        gross_profit=sale.gross_profit.amount,
    )
