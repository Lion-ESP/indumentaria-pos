from __future__ import annotations

import os

DEFAULT_API_URL = "http://localhost:8000"


def get_api_base_url() -> str:
    return os.environ.get("POS_API_URL", DEFAULT_API_URL)
