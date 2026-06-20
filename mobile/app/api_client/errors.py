from __future__ import annotations

import httpx

# Mensajes legibles por code de negocio (los que define el handler de la API).
_FRIENDLY_MESSAGES = {
    "insufficient_stock": "No hay stock suficiente para completar la venta.",
    "payments_do_not_match_total": "Los pagos no coinciden con el total de la venta.",
    "invalid_installments": "La cantidad de cuotas es inválida.",
    "product_not_found": "El producto no existe.",
    "duplicate_sku": "Ya existe un producto con ese SKU.",
}


class ApiError(Exception):
    """Error de negocio devuelto por la API, identificado por su `code` estable."""

    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    @property
    def friendly_message(self) -> str:
        return _FRIENDLY_MESSAGES.get(self.code, self.message)


def raise_for_domain_error(response: httpx.Response) -> None:
    """Traduce respuestas 4xx/5xx a ApiError. Reconoce el sobre de error del
    handler de dominio ({"error": {"code", "message"}}) y la validación de
    FastAPI ({"detail": [...]})."""
    if response.is_success:
        return

    try:
        payload = response.json()
    except ValueError:
        raise ApiError(
            "http_error", response.text or "Error de red", response.status_code
        ) from None

    if isinstance(payload, dict) and "error" in payload:
        error = payload["error"]
        raise ApiError(error["code"], error["message"], response.status_code)

    if isinstance(payload, dict) and "detail" in payload:
        raise ApiError("validation_error", str(payload["detail"]), response.status_code)

    raise ApiError("http_error", str(payload), response.status_code)
