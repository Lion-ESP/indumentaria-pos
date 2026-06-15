from __future__ import annotations

import pytest

from app.inventory.domain.ports import PhotoStorage


@pytest.mark.unit
def test_photo_storage_declara_el_contrato() -> None:
    assert hasattr(PhotoStorage, "save")
    assert hasattr(PhotoStorage, "delete")
