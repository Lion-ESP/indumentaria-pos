from __future__ import annotations

from app.api_client import PosApiClient
from app.config import get_api_base_url


class AppState:
    """Estado de la app: hoy, el cliente HTTP hacia /api. Punto único para
    inyectar un cliente fake en tests o cambiar el base_url."""

    def __init__(self, client: PosApiClient | None = None) -> None:
        self.client = client or PosApiClient(get_api_base_url())
