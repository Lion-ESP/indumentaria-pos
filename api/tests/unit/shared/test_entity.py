from __future__ import annotations

from uuid import uuid4

import pytest

from app.shared.domain.entity import Entity


@pytest.mark.unit
class TestEntity:
    def test_igualdad_por_id(self) -> None:
        shared_id = uuid4()
        assert Entity(id=shared_id) == Entity(id=shared_id)

    def test_distinto_id_distinta_entidad(self) -> None:
        assert Entity(id=uuid4()) != Entity(id=uuid4())

    def test_no_es_igual_a_otro_tipo(self) -> None:
        assert Entity(id=uuid4()) != "no soy una entidad"

    def test_hasheable_por_id(self) -> None:
        shared_id = uuid4()
        assert hash(Entity(id=shared_id)) == hash(Entity(id=shared_id))
