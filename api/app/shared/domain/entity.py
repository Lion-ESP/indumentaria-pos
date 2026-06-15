from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(eq=False)
class Entity:
    """Entidad con identidad: la igualdad es por id, no por valor."""

    id: UUID = field(default_factory=uuid4)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entity) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass(eq=False)
class AggregateRoot(Entity):
    """Raíz de agregado: única puerta de entrada a su consistencia."""
