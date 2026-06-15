from __future__ import annotations


class DomainException(Exception):
    """Raíz de todas las excepciones de negocio. NO conoce HTTP.

    `code` es un identificador estable para el cliente (no traducible);
    la traducción a status HTTP ocurre en el exception handler global.
    """

    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class BusinessRuleViolation(DomainException):
    code = "business_rule_violation"


class EntityNotFound(DomainException):
    code = "entity_not_found"
