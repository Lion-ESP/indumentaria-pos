from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.inventory.domain.exceptions import StockInsuficienteException
from app.sales.domain.exceptions import CuotasInvalidasException, VentaNoCuadraException
from app.shared.domain.exceptions import (
    BusinessRuleViolation,
    DomainException,
    EntityNotFound,
)

# Mapa explícito excepción-de-dominio -> status HTTP. El dominio no conoce HTTP;
# este es el único punto de traducción.
_STATUS_MAP: dict[type[DomainException], int] = {
    EntityNotFound: status.HTTP_404_NOT_FOUND,
    StockInsuficienteException: status.HTTP_409_CONFLICT,
    VentaNoCuadraException: status.HTTP_422_UNPROCESSABLE_ENTITY,
    CuotasInvalidasException: status.HTTP_422_UNPROCESSABLE_ENTITY,
    BusinessRuleViolation: status.HTTP_422_UNPROCESSABLE_ENTITY,
}


def _resolve_status(exc: DomainException) -> int:
    for exc_type, http_status in _STATUS_MAP.items():
        if isinstance(exc, exc_type):
            return http_status
    return status.HTTP_400_BAD_REQUEST


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def handle_domain_exception(request: Request, exc: DomainException) -> JSONResponse:
        return JSONResponse(
            status_code=_resolve_status(exc),
            content={"error": {"code": exc.code, "message": exc.message}},
        )
