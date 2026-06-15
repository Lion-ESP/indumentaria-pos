# PRD — Especificación Técnica y Funcional · `indumentaria-pos`

> **Tipo de documento:** Documento de Especificaciones Técnicas y Funcionales (PRD + Arquitectura)
> **Estado:** Borrador para desarrollo · v1.0
> **Stack:** Python 3.12 · FastAPI · SQLModel/SQLAlchemy · Alembic · SQLite (inicial) · Flet
> **Arquitectura:** Monolito Modular + Arquitectura Hexagonal (Ports & Adapters) + DDD táctico
> **Audiencia:** Equipo de desarrollo, QA, arquitectura.

---

## Tabla de contenidos

1. [Visión y objetivos](#1-visión-y-objetivos)
2. [Principios de arquitectura](#2-principios-de-arquitectura)
3. [Estructura del monorepo](#3-estructura-del-monorepo)
4. [Bounded Contexts (módulos del monolito)](#4-bounded-contexts-módulos-del-monolito)
5. [Capa de Dominio (Core)](#5-capa-de-dominio-core)
6. [Capa de Aplicación (Casos de Uso)](#6-capa-de-aplicación-casos-de-uso)
7. [Capa de Adaptadores (Infraestructura)](#7-capa-de-adaptadores-infraestructura)
8. [Capa de Puertos de Entrada (Entrypoints / API)](#8-capa-de-puertos-de-entrada-entrypoints--api)
9. [Manejo global de excepciones](#9-manejo-global-de-excepciones)
10. [Requerimientos funcionales detallados](#10-requerimientos-funcionales-detallados)
11. [Modelo de datos y persistencia](#11-modelo-de-datos-y-persistencia)
12. [Inyección de dependencias y wiring](#12-inyección-de-dependencias-y-wiring)
13. [Estrategia de testing](#13-estrategia-de-testing)
14. [Decisiones de diseño (ADR resumidos)](#14-decisiones-de-diseño-adr-resumidos)
15. [Roadmap de implementación](#15-roadmap-de-implementación)
16. [Glosario del dominio](#16-glosario-del-dominio)

---

## 1. Visión y objetivos

`indumentaria-pos` es un **Punto de Venta (POS)** para un comercio de indumentaria, diseñado para evolucionar hacia un negocio de **mercería**. La diferencia clave de ese futuro es el manejo de **stock fraccionado** (ej. vender 2,75 metros de cinta o 0,5 kg de lana), por lo que el sistema se diseña **desde el día uno** para soportar unidades de medida continuas (decimales) además de unidades discretas.

### 1.1 Objetivos de negocio

| # | Objetivo | Métrica de éxito |
|---|----------|------------------|
| OB-1 | Registrar ventas de forma rápida y confiable | Venta registrada en < 3 s, con descuento de stock atómico |
| OB-2 | Controlar inventario con unidades dinámicas (unidad / metro / kg) | Stock nunca negativo; soporte decimal sin pérdida de precisión |
| OB-3 | Soportar múltiples métodos de pago y financiación en cuotas | Venta cuadra: `Σ pagos == total`; cuotas descompuestas correctamente |
| OB-4 | Visibilidad financiera (ganancia bruta y neta) | Balances con agregación por período, producto y método de pago |

### 1.2 Objetivos técnicos (no funcionales)

- **Desacoplamiento del framework:** el dominio no conoce FastAPI, SQLAlchemy ni Flet. Se puede cambiar la base de datos (SQLite → PostgreSQL) o el framework web sin tocar el core.
- **Escalabilidad evolutiva:** monolito modular hoy; cada Bounded Context puede extraerse como microservicio mañana sin reescribir la lógica de negocio.
- **Precisión monetaria:** dinero **siempre** en `Decimal` (nunca `float`).
- **Precisión de cantidades:** `int` para unidades discretas, `Decimal`/`Float` controlado para fracciones (mercería).
- **Testabilidad:** el dominio se testea sin I/O (sin DB, sin red, sin filesystem).

---

## 2. Principios de arquitectura

### 2.1 Arquitectura Hexagonal (Ports & Adapters)

```
                          ┌──────────────────────────────────────┐
                          │           ENTRYPOINTS (API)           │
                          │   FastAPI Routers · Pydantic DTOs      │
   HTTP / Flet  ───────►  │   Exception Handlers · Dependencies    │
                          └───────────────┬──────────────────────┘
                                          │ llama (DTO → primitivos)
                          ┌───────────────▼──────────────────────┐
                          │        APPLICATION (Use Cases)         │
                          │   Servicios de aplicación · Orquesta   │
                          │   transacciones · Unit of Work         │
                          └───────────────┬──────────────────────┘
                                          │ depende de PUERTOS (Protocols)
          ┌───────────────────────────────▼───────────────────────────────┐
          │                          DOMAIN (Core)                          │
          │  Entidades · Value Objects · Reglas de negocio                  │
          │  Excepciones de dominio · Interfaces de Repositorio (Ports)     │
          │              ⚠️ CERO dependencias de frameworks                 │
          └───────────────────────────────▲───────────────────────────────┘
                                          │ implementa PUERTOS
                          ┌───────────────┴──────────────────────┐
                          │       ADAPTERS (Infrastructure)        │
                          │  SQLAlchemy/SQLModel Repos · Alembic    │
                          │  Almacenamiento de fotos · Mappers      │
                          └────────────────────────────────────────┘
```

**La Regla de Dependencia:** las flechas de dependencia apuntan **siempre hacia adentro**. El dominio no importa nada de las capas externas. La infraestructura y los entrypoints dependen del dominio, nunca al revés. Esto se logra con **Inversión de Dependencias**: el dominio define *interfaces* (puertos) y la infraestructura las *implementa* (adaptadores).

### 2.2 Reglas de oro (innegociables)

1. **El paquete `domain/` no puede tener un solo `import` de:** `fastapi`, `pydantic`, `sqlalchemy`, `sqlmodel`, `flet`, ni nada de `adapters/` o `entrypoints/`. (Validable con un test de arquitectura — ver §13.4).
2. **Pydantic solo vive en `entrypoints/`** (DTOs de request/response). Las entidades del dominio son `@dataclass` puros de Python.
3. **SQLModel/SQLAlchemy solo vive en `adapters/`** (tablas ORM y repos). Las tablas ORM ≠ entidades de dominio: hay un *mapper* explícito entre ambos.
4. **Las excepciones de dominio son agnósticas de HTTP.** No tienen `status_code`. La traducción a HTTP ocurre en un único exception handler global.
5. **Dinero = `Decimal`. Siempre.**

---

## 3. Estructura del monorepo

```
indumentaria-pos/
├── api/                              # Backend FastAPI (Hexagonal)
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/                          # paquete raíz (import: app.*)
│   │   ├── __init__.py
│   │   ├── main.py                   # App factory FastAPI + wiring
│   │   ├── config.py                 # Settings (pydantic-settings)
│   │   │
│   │   ├── shared/                   # Kernel compartido entre contextos
│   │   │   ├── domain/
│   │   │   │   ├── money.py           # Value Object Money (Decimal)
│   │   │   │   ├── quantity.py        # Value Object Quantity + UnitOfMeasure
│   │   │   │   ├── entity.py          # Base Entity / AggregateRoot
│   │   │   │   └── exceptions.py      # DomainException base
│   │   │   └── adapters/
│   │   │       ├── database.py        # engine, session factory
│   │   │       └── unit_of_work.py
│   │   │
│   │   ├── inventory/                # Bounded Context: Inventario
│   │   │   ├── domain/                # entidades, VOs, excepciones, Protocols
│   │   │   │   ├── entities.py            # Product, StockItem
│   │   │   │   ├── exceptions.py          # StockInsuficienteException, ...
│   │   │   │   └── repositories.py        # ProductRepository (Protocol)
│   │   │   ├── application/           # casos de uso (orquestación)
│   │   │   │   ├── commands.py            # comandos internos (no Pydantic)
│   │   │   │   └── use_cases.py           # CreateProduct, AdjustStock, ...
│   │   │   ├── adapters/              # implementaciones de los puertos
│   │   │   │   ├── models.py              # tablas SQLModel
│   │   │   │   ├── mappers.py             # ORM <-> dominio
│   │   │   │   ├── repositories.py        # SqlProductRepository
│   │   │   │   └── photo_storage.py       # LocalPhotoStorage
│   │   │   └── entrypoints/
│   │   │       ├── schemas.py             # Pydantic DTOs (request/response)
│   │   │       └── router.py              # FastAPI routes
│   │   │
│   │   ├── sales/                    # Bounded Context: Ventas
│   │   │   ├── domain/                # Sale, SaleLine, Payment, Installment...
│   │   │   ├── application/
│   │   │   ├── adapters/
│   │   │   └── entrypoints/
│   │   │
│   │   └── reporting/                # Bounded Context: Balances/Reportes
│   │       ├── domain/
│   │       ├── application/
│   │       ├── adapters/              # read models / queries de agregación
│   │       └── entrypoints/
│   └── tests/
│       ├── unit/                     # dominio puro (sin I/O)
│       ├── integration/              # repos contra SQLite real
│       └── e2e/                      # TestClient in-process (pytest)
│
├── tests-e2e/                       # E2E de caja negra (Bruno) — API corriendo
│   ├── bruno.json                    # config de la colección
│   ├── environments/
│   │   ├── local.bru                 # base_url: http://localhost:8000
│   │   └── test.bru                  # base_url del entorno de test (Harness)
│   ├── inventory/                    # 1 .bru por endpoint
│   ├── sales/
│   ├── reporting/
│   └── flows/
│       └── inventariar-vender-balance.bru   # flujo crítico encadenado
│
├── mobile/                          # Frontend Flet
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── api_client/               # cliente HTTP hacia /api (httpx)
│       ├── views/                    # pantallas Flet
│       ├── components/               # widgets reutilizables
│       └── state/                    # manejo de estado de UI
│
├── docs/
│   └── PRD-indumentaria-pos.md      # este documento
├── AGENTS.md                        # reglas de oro para agentes IA
├── .harness/
│   └── pipeline.yaml                # CI/CD (gates de calidad)
├── docker-compose.yml               # api + (futuro) postgres
└── README.md
```

> **Criterio de organización:** *package-by-feature* (por Bounded Context) y, dentro de cada contexto, *package-by-layer* (`domain` / `application` / `adapters` / `entrypoints`). Esto mantiene la cohesión del dominio y hace evidente qué se extraería como microservicio.
>
> **Convención de nombres (canónica):** el paquete raíz es **`app`** (imports `app.<contexto>.<capa>`), sin layout `src/`. La capa de infraestructura se llama **`adapters`** (no `infrastructure`). Los ejemplos de código de este documento usan estos nombres.

---

## 4. Bounded Contexts (módulos del monolito)

| Contexto | Responsabilidad | Agregado raíz | Depende de |
|----------|-----------------|---------------|------------|
| **`inventory`** | Productos, unidades de medida, fotos, niveles de stock y sus movimientos | `Product` | — |
| **`sales`** | Registro de ventas, líneas, pagos, descomposición de cuotas, descuento de stock | `Sale` | `inventory` (vía puerto, no import directo) |
| **`reporting`** | Balances, ganancia bruta/neta, agregaciones por período | (read-only) | lee de `sales` e `inventory` |
| **`shared`** | Kernel: `Money`, `Quantity`, `UnitOfMeasure`, base `Entity`, `DomainException`, UoW, DB | — | — |

### 4.1 Comunicación entre contextos

- **Hoy (monolito):** `sales` no importa entidades de `inventory` directamente. Define en su propio dominio un **puerto** `StockPort` (Protocol) que necesita (`reservar_stock`, `descontar_stock`, `consultar_disponible`). La implementación de ese puerto en infraestructura llama al caso de uso de `inventory`. Así el acoplamiento es por contrato, no por clase concreta.
- **Mañana (microservicios):** ese mismo `StockPort` se reimplementa como cliente HTTP/gRPC sin tocar la lógica de `sales`.

> **Eventos de dominio (opcional, recomendado):** `SaleConfirmed` puede emitirse para que `inventory` descuente stock de forma desacoplada. En v1 se hace síncrono dentro de la misma transacción (Unit of Work) para garantizar atomicidad; los eventos se documentan como evolución futura.

---

## 5. Capa de Dominio (Core)

El corazón del sistema. **Cero dependencias externas.** Solo `dataclasses`, `decimal`, `enum`, `datetime`, `typing`, `abc`.

### 5.1 Value Objects compartidos (`shared/domain`)

#### `Money` — dinero como `Decimal`

```python
# shared/domain/money.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

CENTS = Decimal("0.01")

@dataclass(frozen=True, slots=True)
class Money:
    """Valor monetario inmutable. Internamente SIEMPRE Decimal.
    Redondeo bancario a 2 decimales en construcción y operaciones."""
    amount: Decimal

    def __post_init__(self) -> None:
        # Normaliza a Decimal y cuantiza a centavos.
        object.__setattr__(self, "amount",
                           Decimal(self.amount).quantize(CENTS, rounding=ROUND_HALF_UP))

    @classmethod
    def zero(cls) -> "Money":
        return cls(Decimal("0"))

    def __add__(self, other: "Money") -> "Money":
        return Money(self.amount + other.amount)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.amount - other.amount)

    def multiply(self, factor: Decimal | int) -> "Money":
        return Money(self.amount * Decimal(factor))

    def is_negative(self) -> bool:
        return self.amount < 0
```

> **Por qué no `float`:** `0.1 + 0.2 != 0.3` en flotante binario. En dinero eso genera descuadres. `Decimal` es exacto en base 10.

#### `UnitOfMeasure` y `Quantity` — el núcleo de la mercería

```python
# shared/domain/quantity.py
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

class UnitOfMeasure(str, Enum):
    UNIT = "unit"      # discreta: indumentaria (no admite fracción)
    METER = "meter"    # continua: cinta, tela (mercería)
    KILOGRAM = "kg"    # continua: lana, botones a granel (mercería)

    @property
    def is_fractional(self) -> bool:
        """True si admite cantidades decimales."""
        return self in (UnitOfMeasure.METER, UnitOfMeasure.KILOGRAM)

@dataclass(frozen=True, slots=True)
class Quantity:
    """Cantidad con su unidad. Valida fraccionabilidad según la unidad.
    Diseñado para mercería: METER/KG admiten Decimal; UNIT no."""
    value: Decimal
    unit: UnitOfMeasure

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", Decimal(self.value))
        if self.value < 0:
            raise ValueError("Quantity no puede ser negativa")
        if not self.unit.is_fractional and self.value != self.value.to_integral_value():
            raise ValueError(f"La unidad {self.unit.value} no admite cantidades fraccionadas")

    def add(self, other: "Quantity") -> "Quantity":
        self._assert_same_unit(other)
        return Quantity(self.value + other.value, self.unit)

    def subtract(self, other: "Quantity") -> "Quantity":
        self._assert_same_unit(other)
        return Quantity(self.value - other.value, self.unit)

    def is_enough_for(self, requested: "Quantity") -> bool:
        self._assert_same_unit(requested)
        return self.value >= requested.value

    def _assert_same_unit(self, other: "Quantity") -> None:
        if self.unit != other.unit:
            raise ValueError(f"Unidades incompatibles: {self.unit} vs {other.unit}")
```

> **Nota sobre `Float` vs `Decimal` para cantidades:** el enunciado menciona `Float` para stock fraccionado. **Recomendación arquitectónica:** usar `Decimal` también para cantidades, por las mismas razones que el dinero (precisión exacta, sin errores de redondeo al sumar movimientos de stock). En la **persistencia** la columna puede ser `Numeric/Decimal`; si se exige `Float` por un requisito de almacenamiento, se aísla en la capa de infra y el dominio sigue operando con `Decimal`. Esto está registrado como decisión **ADR-003** (§14).

#### Base `Entity` / `AggregateRoot`

```python
# shared/domain/entity.py
from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass(eq=False)
class Entity:
    """Identidad por id, no por valor."""
    id: UUID = field(default_factory=uuid4)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entity) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

@dataclass(eq=False)
class AggregateRoot(Entity):
    """Raíz de agregado: única puerta de entrada a su consistencia."""
```

### 5.2 Excepciones de dominio (`shared` + por contexto)

```python
# shared/domain/exceptions.py
class DomainException(Exception):
    """Raíz de todas las excepciones de negocio. NO conoce HTTP.
    code: identificador estable para el cliente (no traducible)."""
    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

class BusinessRuleViolation(DomainException):
    code = "business_rule_violation"

class EntityNotFound(DomainException):
    code = "entity_not_found"
```

```python
# inventory/domain/exceptions.py
from app.shared.domain.exceptions import DomainException, EntityNotFound

class ProductNotFound(EntityNotFound):
    code = "product_not_found"

class StockInsuficienteException(DomainException):
    code = "insufficient_stock"
    def __init__(self, sku: str, requested, available) -> None:
        super().__init__(
            f"Stock insuficiente para '{sku}': solicitado {requested}, disponible {available}"
        )
        self.sku = sku
        self.requested = requested
        self.available = available

class UnidadDeMedidaInvalida(DomainException):
    code = "invalid_unit_of_measure"
```

```python
# sales/domain/exceptions.py
from app.shared.domain.exceptions import DomainException

class VentaNoCuadraException(DomainException):
    """La suma de pagos no coincide con el total de la venta."""
    code = "payments_do_not_match_total"

class CuotasInvalidasException(DomainException):
    code = "invalid_installments"

class MetodoDePagoNoSoportado(DomainException):
    code = "unsupported_payment_method"
```

### 5.3 Entidades del dominio

#### Contexto `inventory`

```python
# inventory/domain/entities.py
from __future__ import annotations
from dataclasses import dataclass, field
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure
from app.inventory.domain.exceptions import StockInsuficienteException

@dataclass(eq=False)
class Product(AggregateRoot):
    sku: str = ""
    name: str = ""
    unit: UnitOfMeasure = UnitOfMeasure.UNIT
    cost_price: Money = field(default_factory=Money.zero)   # precio de costo
    sale_price: Money = field(default_factory=Money.zero)   # precio de venta
    stock: Quantity = None                                  # nivel actual
    photo_path: str | None = None
    active: bool = True

    def __post_init__(self) -> None:
        if self.stock is None:
            self.stock = Quantity(0, self.unit)

    @property
    def gross_margin_unit(self) -> Money:
        """Ganancia bruta por unidad = venta - costo."""
        return self.sale_price - self.cost_price

    def can_fulfill(self, requested: Quantity) -> bool:
        return self.stock.is_enough_for(requested)

    def decrease_stock(self, requested: Quantity) -> None:
        if not self.can_fulfill(requested):
            raise StockInsuficienteException(self.sku, requested.value, self.stock.value)
        self.stock = self.stock.subtract(requested)

    def increase_stock(self, amount: Quantity) -> None:
        self.stock = self.stock.add(amount)
```

#### Contexto `sales`

```python
# sales/domain/entities.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum
from uuid import UUID
from app.shared.domain.entity import AggregateRoot
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity
from app.sales.domain.exceptions import VentaNoCuadraException, CuotasInvalidasException

class PaymentMethod(str, Enum):
    CASH = "cash"
    DEBIT = "debit"
    CREDIT_CARD = "credit_card"
    TRANSFER = "transfer"

@dataclass(frozen=True, slots=True)
class Installment:
    """Una cuota de un pago con tarjeta."""
    number: int          # 1..n
    amount: Money
    due_date: date

@dataclass
class Payment:
    """Un pago dentro de una venta. Si es tarjeta en cuotas, se descompone."""
    method: PaymentMethod
    amount: Money
    installments_count: int = 1
    surcharge_rate: Decimal = Decimal("0")  # recargo financiero (ej. 0.15 = 15%)
    installments: list[Installment] = field(default_factory=list)

    @property
    def total_with_surcharge(self) -> Money:
        return self.amount.multiply(Decimal("1") + self.surcharge_rate)

@dataclass
class SaleLine:
    product_id: UUID
    sku: str
    quantity: Quantity
    unit_sale_price: Money
    unit_cost_price: Money   # congelado al momento de la venta (snapshot)

    @property
    def subtotal(self) -> Money:
        return self.unit_sale_price.multiply(self.quantity.value)

    @property
    def line_cost(self) -> Money:
        return self.unit_cost_price.multiply(self.quantity.value)

    @property
    def gross_profit(self) -> Money:
        return self.subtotal - self.line_cost

@dataclass(eq=False)
class Sale(AggregateRoot):
    created_at: date = field(default_factory=date.today)
    lines: list[SaleLine] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list)

    @property
    def total(self) -> Money:
        total = Money.zero()
        for line in self.lines:
            total = total + line.subtotal
        return total

    @property
    def total_paid(self) -> Money:
        paid = Money.zero()
        for p in self.payments:
            paid = paid + p.amount
        return paid

    @property
    def gross_profit(self) -> Money:
        profit = Money.zero()
        for line in self.lines:
            profit = profit + line.gross_profit
        return profit

    def validate(self) -> None:
        """Invariante de agregado: la venta debe cuadrar."""
        if not self.lines:
            raise VentaNoCuadraException("La venta no tiene líneas")
        if self.total_paid.amount != self.total.amount:
            raise VentaNoCuadraException(
                f"Pagos ({self.total_paid.amount}) != total ({self.total.amount})"
            )
        for payment in self.payments:
            if payment.installments_count < 1:
                raise CuotasInvalidasException("Cantidad de cuotas inválida")
```

### 5.4 Servicios de dominio (lógica que no pertenece a una sola entidad)

```python
# sales/domain/services.py
from datetime import date
from dateutil.relativedelta import relativedelta   # OJO: dateutil es puro, sin framework
from decimal import Decimal, ROUND_HALF_UP
from app.shared.domain.money import Money, CENTS
from app.sales.domain.entities import Payment, Installment, PaymentMethod
from app.sales.domain.exceptions import CuotasInvalidasException

class InstallmentCalculator:
    """Descompone un pago con tarjeta en N cuotas, repartiendo centavos
    de redondeo en la última cuota para que Σ cuotas == monto total exacto."""

    def build(self, payment: Payment, first_due: date) -> list[Installment]:
        if payment.method != PaymentMethod.CREDIT_CARD:
            return []
        n = payment.installments_count
        if n < 1:
            raise CuotasInvalidasException("Cuotas debe ser >= 1")

        total = payment.total_with_surcharge.amount
        base = (total / n).quantize(CENTS, rounding=ROUND_HALF_UP)
        installments: list[Installment] = []
        accumulated = Decimal("0")
        for i in range(1, n + 1):
            if i < n:
                amount = base
            else:
                amount = (total - accumulated)  # última cuota absorbe el redondeo
            accumulated += amount
            installments.append(
                Installment(number=i, amount=Money(amount),
                            due_date=first_due + relativedelta(months=i - 1))
            )
        return installments
```

> **Por qué la última cuota absorbe el redondeo:** si `total = 100,00` en 3 cuotas, `100/3 = 33,3333…`. Cuotas de `33,33 + 33,33 + 33,34 = 100,00`. Sin esta corrección, `33,33 × 3 = 99,99` y la venta no cuadra.

### 5.5 Puertos de salida (interfaces de repositorio)

Definidos con `typing.Protocol` (structural typing) en el dominio. La infraestructura los implementa sin heredarlos explícitamente.

```python
# inventory/domain/repositories.py
from __future__ import annotations
from typing import Protocol
from uuid import UUID
from app.inventory.domain.entities import Product

class ProductRepository(Protocol):
    def get(self, product_id: UUID) -> Product | None: ...
    def get_by_sku(self, sku: str) -> Product | None: ...
    def list_active(self) -> list[Product]: ...
    def add(self, product: Product) -> None: ...
    def update(self, product: Product) -> None: ...
```

```python
# inventory/domain/ports.py
from typing import Protocol

class PhotoStorage(Protocol):
    """Puerto de salida para almacenar fotos de producto."""
    def save(self, product_sku: str, content: bytes, filename: str) -> str:
        """Devuelve la ruta/URL persistida."""
        ...
    def delete(self, path: str) -> None: ...
```

```python
# sales/domain/repositories.py
from typing import Protocol
from uuid import UUID
from app.sales.domain.entities import Sale

class SaleRepository(Protocol):
    def get(self, sale_id: UUID) -> Sale | None: ...
    def add(self, sale: Sale) -> None: ...
```

```python
# sales/domain/ports.py  (puerto hacia el contexto inventory)
from typing import Protocol
from uuid import UUID
from app.shared.domain.quantity import Quantity
from app.shared.domain.money import Money

class StockPort(Protocol):
    """Lo que 'sales' necesita de 'inventory', sin acoplarse a sus clases."""
    def get_pricing(self, product_id: UUID) -> tuple[Money, Money]:
        """(sale_price, cost_price) congelados al momento de la venta."""
        ...
    def decrease_stock(self, product_id: UUID, quantity: Quantity) -> None:
        """Lanza StockInsuficienteException si no alcanza."""
        ...
```

---

## 6. Capa de Aplicación (Casos de Uso)

Orquesta el dominio y la persistencia. **No contiene reglas de negocio** (esas viven en las entidades/servicios de dominio); coordina: abre transacción, carga agregados, invoca comportamiento, persiste, confirma.

```python
# sales/application/use_cases.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure
from app.shared.adapters.unit_of_work import UnitOfWork
from app.sales.domain.entities import Sale, SaleLine, Payment, PaymentMethod
from app.sales.domain.services import InstallmentCalculator
from app.sales.domain.ports import StockPort

# --- Comandos de aplicación: dataclasses puros, NO Pydantic ---
@dataclass(frozen=True)
class LineCommand:
    product_id: UUID
    quantity: Decimal

@dataclass(frozen=True)
class PaymentCommand:
    method: str
    amount: Decimal
    installments_count: int = 1
    surcharge_rate: Decimal = Decimal("0")

@dataclass(frozen=True)
class RegisterSaleCommand:
    lines: list[LineCommand]
    payments: list[PaymentCommand]

class RegisterSaleUseCase:
    """Caso de uso: registrar una venta de forma transaccional y atómica.
    1. Construye el agregado Sale con precios congelados desde inventory.
    2. Valida invariantes (la venta cuadra).
    3. Descuenta stock (puede lanzar StockInsuficienteException).
    4. Persiste todo dentro de una sola Unit of Work."""

    def __init__(self, uow: UnitOfWork, stock: StockPort,
                 installments: InstallmentCalculator) -> None:
        self._uow = uow
        self._stock = stock
        self._installments = installments

    def execute(self, command: RegisterSaleCommand) -> UUID:
        with self._uow:
            sale = Sale()
            for line in command.lines:
                sale_price, cost_price = self._stock.get_pricing(line.product_id)
                # La unidad real del producto la conoce inventory; aquí se asume
                # que get_pricing podría devolver también la unidad. Simplificado:
                sale.lines.append(SaleLine(
                    product_id=line.product_id,
                    sku=str(line.product_id),
                    quantity=Quantity(line.quantity, UnitOfMeasure.UNIT),
                    unit_sale_price=sale_price,
                    unit_cost_price=cost_price,
                ))

            for p in command.payments:
                payment = Payment(
                    method=PaymentMethod(p.method),
                    amount=Money(p.amount),
                    installments_count=p.installments_count,
                    surcharge_rate=p.surcharge_rate,
                )
                payment.installments = self._installments.build(payment, date.today())
                sale.payments.append(payment)

            sale.validate()  # invariante: pagos == total

            for line in sale.lines:
                self._stock.decrease_stock(line.product_id, line.quantity)

            self._uow.sales.add(sale)
            self._uow.commit()
            return sale.id
```

> **Patrón Unit of Work:** garantiza que el descuento de stock y la persistencia de la venta sean **atómicos**. Si el descuento de stock falla a la mitad, el `with` hace rollback de todo. Esto es crítico: nunca debe quedar una venta registrada sin haber descontado stock, ni stock descontado sin venta.

---

## 7. Capa de Adaptadores (Infraestructura)

### 7.1 Tablas ORM con SQLModel (separadas de las entidades)

```python
# inventory/adapters/models.py
from decimal import Decimal
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class ProductModel(SQLModel, table=True):
    __tablename__ = "products"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    sku: str = Field(index=True, unique=True)
    name: str
    unit: str                                   # 'unit' | 'meter' | 'kg'
    cost_price: Decimal = Field(max_digits=12, decimal_places=2)
    sale_price: Decimal = Field(max_digits=12, decimal_places=2)
    stock_value: Decimal = Field(max_digits=14, decimal_places=3)  # soporta fracción
    photo_path: str | None = None
    active: bool = True
```

> **Precisión en DB:** `cost_price`/`sale_price` → `NUMERIC(12,2)`. `stock_value` → `NUMERIC(14,3)` para soportar fracciones de mercería (3 decimales: ej. 2,750 metros). **No `FLOAT`** en columnas; SQLite mapea `NUMERIC` y se preserva precisión vía `Decimal` en Python.

### 7.2 Mapper explícito ORM ↔ Dominio

```python
# inventory/adapters/mappers.py
from app.inventory.domain.entities import Product
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure
from app.inventory.adapters.models import ProductModel

def to_domain(row: ProductModel) -> Product:
    unit = UnitOfMeasure(row.unit)
    return Product(
        id=row.id, sku=row.sku, name=row.name, unit=unit,
        cost_price=Money(row.cost_price), sale_price=Money(row.sale_price),
        stock=Quantity(row.stock_value, unit),
        photo_path=row.photo_path, active=row.active,
    )

def to_model(p: Product) -> ProductModel:
    return ProductModel(
        id=p.id, sku=p.sku, name=p.name, unit=p.unit.value,
        cost_price=p.cost_price.amount, sale_price=p.sale_price.amount,
        stock_value=p.stock.value, photo_path=p.photo_path, active=p.active,
    )
```

> **Por qué un mapper y no usar la tabla como entidad:** acoplar la entidad de dominio al ORM ata el modelo de negocio al esquema de DB y a SQLModel. El mapper cuesta algo de boilerplate pero preserva la regla de dependencia y permite que el dominio evolucione independientemente del esquema.

### 7.3 Implementación de repositorios

```python
# inventory/adapters/repositories.py
from uuid import UUID
from sqlmodel import Session, select
from app.inventory.domain.entities import Product
from app.inventory.adapters.models import ProductModel
from app.inventory.adapters import mappers

class SqlProductRepository:
    """Implementa el Protocol ProductRepository (structural typing)."""
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, product_id: UUID) -> Product | None:
        row = self._session.get(ProductModel, product_id)
        return mappers.to_domain(row) if row else None

    def get_by_sku(self, sku: str) -> Product | None:
        row = self._session.exec(
            select(ProductModel).where(ProductModel.sku == sku)
        ).first()
        return mappers.to_domain(row) if row else None

    def list_active(self) -> list[Product]:
        rows = self._session.exec(
            select(ProductModel).where(ProductModel.active == True)  # noqa: E712
        ).all()
        return [mappers.to_domain(r) for r in rows]

    def add(self, product: Product) -> None:
        self._session.add(mappers.to_model(product))

    def update(self, product: Product) -> None:
        row = self._session.get(ProductModel, product.id)
        updated = mappers.to_model(product)
        for field, value in updated.model_dump().items():
            setattr(row, field, value)
```

### 7.4 Unit of Work

```python
# shared/adapters/unit_of_work.py
from __future__ import annotations
from sqlmodel import Session
from app.inventory.adapters.repositories import SqlProductRepository
from app.sales.adapters.repositories import SqlSaleRepository

class UnitOfWork:
    """Agrupa repos sobre una misma sesión/transacción. Context manager."""
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def __enter__(self) -> "UnitOfWork":
        self._session: Session = self._session_factory()
        self.products = SqlProductRepository(self._session)
        self.sales = SqlSaleRepository(self._session)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.rollback()
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
```

### 7.5 Almacenamiento local de fotos

```python
# inventory/adapters/photo_storage.py
from pathlib import Path
from app.config import Settings  # ruta base configurable

class LocalPhotoStorage:
    """Implementa el Protocol PhotoStorage. Guarda en disco local.
    Migrable a S3/MinIO reimplementando el mismo puerto."""
    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, product_sku: str, content: bytes, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        dest = self._base / f"{product_sku}{ext}"
        dest.write_bytes(content)
        return str(dest.relative_to(self._base.parent))

    def delete(self, path: str) -> None:
        target = self._base.parent / path
        target.unlink(missing_ok=True)
```

### 7.6 Migraciones con Alembic

- `alembic/env.py` importa `SQLModel.metadata` (target_metadata) de todos los `*/adapters/models.py`.
- Flujo: `alembic revision --autogenerate -m "descripción"` → revisar el script generado (Alembic no detecta todo: renombres, cambios de tipo) → `alembic upgrade head`.
- **Regla:** las migraciones se versionan en git y se aplican en orden. Nunca editar una migración ya aplicada en otro entorno.
- Para SQLite: cuidar `batch_mode` en `env.py` (`render_as_batch=True`) porque SQLite no soporta `ALTER COLUMN` nativo.

---

## 8. Capa de Puertos de Entrada (Entrypoints / API)

### 8.1 DTOs Pydantic (solo aquí vive Pydantic)

```python
# inventory/entrypoints/schemas.py
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class CreateProductRequest(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1)
    unit: str = Field(pattern="^(unit|meter|kg)$")
    cost_price: Decimal = Field(ge=0, decimal_places=2)
    sale_price: Decimal = Field(ge=0, decimal_places=2)
    initial_stock: Decimal = Field(ge=0, default=Decimal("0"))

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    sku: str
    name: str
    unit: str
    cost_price: Decimal
    sale_price: Decimal
    stock: Decimal
    gross_margin_unit: Decimal
```

```python
# sales/entrypoints/schemas.py
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

class SaleLineRequest(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(gt=0)

class PaymentRequest(BaseModel):
    method: str = Field(pattern="^(cash|debit|credit_card|transfer)$")
    amount: Decimal = Field(gt=0)
    installments_count: int = Field(ge=1, default=1)
    surcharge_rate: Decimal = Field(ge=0, default=Decimal("0"))

class RegisterSaleRequest(BaseModel):
    lines: list[SaleLineRequest] = Field(min_length=1)
    payments: list[PaymentRequest] = Field(min_length=1)

class SaleResponse(BaseModel):
    id: UUID
    total: Decimal
    total_paid: Decimal
    gross_profit: Decimal
```

### 8.2 Routers FastAPI

```python
# sales/entrypoints/router.py
from fastapi import APIRouter, Depends, status
from app.sales.entrypoints.schemas import RegisterSaleRequest, SaleResponse
from app.sales.application.use_cases import (
    RegisterSaleUseCase, RegisterSaleCommand, LineCommand, PaymentCommand,
)
from app.sales.entrypoints.dependencies import get_register_sale_use_case

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
def register_sale(
    body: RegisterSaleRequest,
    use_case: RegisterSaleUseCase = Depends(get_register_sale_use_case),
) -> SaleResponse:
    command = RegisterSaleCommand(
        lines=[LineCommand(l.product_id, l.quantity) for l in body.lines],
        payments=[PaymentCommand(p.method, p.amount, p.installments_count,
                                 p.surcharge_rate) for p in body.payments],
    )
    sale_id = use_case.execute(command)   # puede lanzar excepciones de dominio
    # ... recuperar la venta para armar el response (o el UC devuelve un read DTO)
    ...
```

> **Frontera de traducción:** el router convierte `Request (Pydantic)` → `Command (dataclass)`. El caso de uso **nunca** ve Pydantic. La respuesta hace el camino inverso: dominio → `Response (Pydantic)`.

---

## 9. Manejo global de excepciones

Único punto donde las excepciones de dominio se traducen a HTTP. El dominio **no sabe** qué status code le corresponde.

```python
# shared/adapters/exception_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.shared.domain.exceptions import (
    DomainException, EntityNotFound, BusinessRuleViolation,
)
from app.inventory.domain.exceptions import StockInsuficienteException
from app.sales.domain.exceptions import VentaNoCuadraException, CuotasInvalidasException

# Mapa explícito excepción-de-dominio -> status HTTP
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
    return status.HTTP_400_BAD_REQUEST  # fallback para DomainException genérica

def register_exception_handlers(app) -> None:
    @app.exception_handler(DomainException)
    async def handle_domain_exception(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=_resolve_status(exc),
            content={
                "error": {
                    "code": exc.code,       # estable, para el cliente Flet
                    "message": exc.message, # legible
                }
            },
        )
```

| Excepción de dominio | Código (`code`) | HTTP |
|----------------------|-----------------|------|
| `ProductNotFound` / `EntityNotFound` | `entity_not_found` | `404 Not Found` |
| `StockInsuficienteException` | `insufficient_stock` | `409 Conflict` |
| `VentaNoCuadraException` | `payments_do_not_match_total` | `422 Unprocessable Entity` |
| `CuotasInvalidasException` | `invalid_installments` | `422 Unprocessable Entity` |
| `BusinessRuleViolation` (genérica) | `business_rule_violation` | `422` |
| `DomainException` (fallback) | `domain_error` | `400 Bad Request` |
| `RequestValidationError` (Pydantic) | — | `422` (handler nativo FastAPI) |

> **Beneficio:** agregar una nueva regla de negocio nunca obliga a tocar los routers. Solo se define la excepción en el dominio y, si necesita un status particular, se agrega una línea al `_STATUS_MAP`.

---

## 10. Requerimientos funcionales detallados

### RF-1 · Inventario con unidades de medida dinámicas

| ID | Requerimiento | Regla / Criterio de aceptación |
|----|---------------|-------------------------------|
| RF-1.1 | Alta de producto con unidad de medida (`unit`, `meter`, `kg`) | El producto persiste su unidad; condiciona la fraccionabilidad del stock |
| RF-1.2 | Stock fraccionado para `meter`/`kg` | Aceptar cantidades decimales (ej. 2,750). Rechazar fracciones en `unit` con `400` |
| RF-1.3 | Ajuste de stock (entrada/salida) | `increase_stock` / `decrease_stock` validan unidad y no permiten negativo |
| RF-1.4 | Foto de producto | Upload `multipart/form-data`; se guarda vía `PhotoStorage`; ruta persistida en el producto |
| RF-1.5 | Consulta de stock disponible | Endpoint de lectura devuelve `stock` con su unidad |

**Endpoints:**
```
POST   /products                 # alta (CreateProductRequest)
GET    /products                 # listado de activos
GET    /products/{id}            # detalle
POST   /products/{id}/stock      # ajuste (+/-)
POST   /products/{id}/photo      # upload foto (multipart)
```

### RF-2 · Registro de ventas con múltiples métodos de pago y cuotas

| ID | Requerimiento | Regla / Criterio de aceptación |
|----|---------------|-------------------------------|
| RF-2.1 | Venta con N líneas | Cada línea referencia un producto, cantidad y precios congelados (snapshot de costo y venta al momento) |
| RF-2.2 | Múltiples pagos por venta | Una venta admite varios `Payment` (ej. parte efectivo + parte tarjeta) |
| RF-2.3 | La venta debe cuadrar | `Σ payments.amount == total`; si no, `VentaNoCuadraException` → `422` |
| RF-2.4 | Descomposición de cuotas (tarjeta de crédito) | `InstallmentCalculator` genera N cuotas; última absorbe el redondeo; `Σ cuotas == monto con recargo` |
| RF-2.5 | Recargo financiero por financiación | `surcharge_rate` aplica sobre el monto del pago con tarjeta |
| RF-2.6 | Descuento de stock atómico | El stock se descuenta en la misma transacción (UoW); si falla, rollback total |
| RF-2.7 | Stock insuficiente | `StockInsuficienteException` → `409 Conflict`; la venta NO se registra |

**Endpoint:**
```
POST   /sales                    # RegisterSaleRequest -> 201 SaleResponse
GET    /sales/{id}               # detalle con líneas, pagos y cuotas
```

**Ejemplo de payload `POST /sales`:**
```json
{
  "lines": [
    { "product_id": "uuid-remera", "quantity": "2" },
    { "product_id": "uuid-cinta",  "quantity": "2.750" }
  ],
  "payments": [
    { "method": "cash", "amount": "5000.00" },
    { "method": "credit_card", "amount": "12000.00",
      "installments_count": 3, "surcharge_rate": "0.15" }
  ]
}
```

### RF-3 · Balances con ganancia bruta y neta

| ID | Requerimiento | Regla / Criterio de aceptación |
|----|---------------|-------------------------------|
| RF-3.1 | Ganancia bruta por período | `Σ (precio_venta − precio_costo) × cantidad` sobre ventas del rango |
| RF-3.2 | Ganancia neta | Ganancia bruta − costos financieros (recargos absorbidos) − egresos/gastos registrados |
| RF-3.3 | Agregación por dimensión | Por día/mes, por producto, por método de pago |
| RF-3.4 | Reporte de cobranza futura | Proyección de cuotas a cobrar por mes (a partir de `Installment.due_date`) |

> **Diseño del contexto `reporting`:** es de **solo lectura** y usa *read models* / queries de agregación optimizadas (no carga agregados completos). Puede leer directamente proyecciones SQL sin pasar por los repos transaccionales, ya que no muta estado. Esto evita el sobrecosto de hidratar agregados para reportar.

**Endpoints:**
```
GET /reports/balance?from=2026-01-01&to=2026-01-31&group_by=day
GET /reports/profit?from=...&to=...&group_by=product
GET /reports/receivables?month=2026-07         # cuotas a cobrar
```

**Concepto de cálculo de ganancia (dominio de reporting):**
```python
# Ganancia bruta de una venta = Σ líneas (subtotal - line_cost)
# Ganancia neta = ganancia bruta - recargos financieros - gastos del período
gross = sum((line.gross_profit for line in sale.lines), Money.zero())
net   = gross - financial_costs - operating_expenses
```

---

## 11. Modelo de datos y persistencia

### 11.1 Tablas principales

| Tabla | Columnas clave | Tipos sensibles |
|-------|----------------|-----------------|
| `products` | `id`, `sku` (unique), `unit`, `cost_price`, `sale_price`, `stock_value`, `photo_path`, `active` | `cost_price`/`sale_price` → `NUMERIC(12,2)`; `stock_value` → `NUMERIC(14,3)` |
| `stock_movements` | `id`, `product_id`, `delta`, `reason`, `created_at` | `delta` → `NUMERIC(14,3)` (auditoría de stock) |
| `sales` | `id`, `created_at`, `total`, `gross_profit` | `NUMERIC(12,2)` |
| `sale_lines` | `id`, `sale_id`, `product_id`, `sku`, `quantity`, `unit_sale_price`, `unit_cost_price` | precios congelados (snapshot) |
| `payments` | `id`, `sale_id`, `method`, `amount`, `installments_count`, `surcharge_rate` | — |
| `installments` | `id`, `payment_id`, `number`, `amount`, `due_date` | — |

### 11.2 Reglas de persistencia

- **Precios congelados (snapshot):** `sale_lines` guarda el `unit_cost_price` y `unit_sale_price` vigentes al momento de la venta. Si luego cambia el precio del producto, los reportes históricos no se distorsionan.
- **Auditoría de stock:** cada ajuste o venta genera un `stock_movement`. El `stock_value` del producto es el saldo; los movimientos son el libro mayor (permite reconstruir y auditar).
- **Migración SQLite → PostgreSQL:** como el dominio no conoce el motor y los tipos son `NUMERIC`/`UUID` estándar, el cambio se reduce a la cadena de conexión y revisar `render_as_batch` de Alembic.

---

## 12. Inyección de dependencias y wiring

FastAPI `Depends` ensambla los adaptadores concretos con los casos de uso. El wiring es el **único lugar** que conoce simultáneamente dominio e infraestructura.

```python
# sales/entrypoints/dependencies.py
from app.shared.adapters.database import session_factory
from app.shared.adapters.unit_of_work import UnitOfWork
from app.sales.application.use_cases import RegisterSaleUseCase
from app.sales.domain.services import InstallmentCalculator
from app.sales.adapters.stock_adapter import InventoryStockAdapter

def get_register_sale_use_case() -> RegisterSaleUseCase:
    uow = UnitOfWork(session_factory)
    stock = InventoryStockAdapter(session_factory)  # implementa StockPort
    return RegisterSaleUseCase(uow, stock, InstallmentCalculator())
```

```python
# main.py — app factory
from fastapi import FastAPI
from app.inventory.entrypoints.router import router as inventory_router
from app.sales.entrypoints.router import router as sales_router
from app.reporting.entrypoints.router import router as reporting_router
from app.shared.adapters.exception_handlers import register_exception_handlers

def create_app() -> FastAPI:
    app = FastAPI(title="indumentaria-pos", version="1.0.0")
    register_exception_handlers(app)
    app.include_router(inventory_router)
    app.include_router(sales_router)
    app.include_router(reporting_router)
    return app

app = create_app()
```

---

## 13. Estrategia de testing

### 13.1 Pirámide

| Nivel | Qué prueba | Sin I/O | Herramienta |
|-------|------------|---------|-------------|
| **Unit (dominio)** | Entidades, VOs, servicios (ej. `InstallmentCalculator`, `Sale.validate`) | ✅ sí | `pytest` puro |
| **Integration** | Repos contra SQLite real, mappers, UoW | ❌ DB real (in-memory) | `pytest` + SQLite `:memory:` |
| **E2E / API (in-process)** | Endpoints completos sin servidor | ❌ | `pytest` + `TestClient` |
| **E2E de caja negra (regresión)** | API **corriendo**: contrato + flujo crítico | ❌ servidor real | **Bruno** (`.bru` + `bru run`) |

> **Dos capas E2E, roles distintos (no se solapan):** el E2E *in-process* (`TestClient`) es la red de seguridad rápida del dev y cuenta para coverage. El E2E *de caja negra* (Bruno) valida la API ya desplegada contra un entorno real — regresión post-deploy y suite de contrato viva mantenida por QA y el agente Bruno en texto plano. Detalle operativo en `docs/PLAN-desarrollo-y-testing.md`.

### 13.2 Ejemplos de tests de dominio (rápidos, sin DB)

```python
def test_descompone_3_cuotas_y_la_ultima_absorbe_el_redondeo():
    payment = Payment(method=PaymentMethod.CREDIT_CARD,
                      amount=Money(Decimal("100.00")), installments_count=3)
    cuotas = InstallmentCalculator().build(payment, date(2026, 1, 1))
    montos = [c.amount.amount for c in cuotas]
    assert montos == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
    assert sum(montos) == Decimal("100.00")

def test_venta_que_no_cuadra_lanza_excepcion():
    sale = Sale()
    sale.lines.append(SaleLine(product_id=uuid4(), sku="X",
        quantity=Quantity(1, UnitOfMeasure.UNIT),
        unit_sale_price=Money(Decimal("100.00")),
        unit_cost_price=Money(Decimal("60.00"))))
    sale.payments.append(Payment(PaymentMethod.CASH, Money(Decimal("90.00"))))
    with pytest.raises(VentaNoCuadraException):
        sale.validate()

def test_unidad_discreta_rechaza_fraccion():
    with pytest.raises(ValueError):
        Quantity(Decimal("2.5"), UnitOfMeasure.UNIT)

def test_metro_admite_fraccion():
    q = Quantity(Decimal("2.750"), UnitOfMeasure.METER)
    assert q.value == Decimal("2.750")
```

### 13.3 Tests de integración con repos

- Usar SQLite `:memory:` + `SQLModel.metadata.create_all`.
- Verificar round-trip: `add` → `get` → entidad equivalente (incluyendo precisión `Decimal`).

### 13.4 Test de arquitectura (guardia de la regla de dependencia)

```python
def test_dominio_no_importa_frameworks():
    """El paquete domain no debe importar fastapi/pydantic/sqlalchemy/sqlmodel/flet."""
    import ast, pathlib
    prohibidos = {"fastapi", "pydantic", "sqlalchemy", "sqlmodel", "flet"}
    for path in pathlib.Path("app").rglob("domain/**/*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = (node.module or "").split(".")[0] if isinstance(node, ast.ImportFrom) \
                      else node.names[0].name.split(".")[0]
                assert mod not in prohibidos, f"{path} importa {mod} (prohibido en dominio)"
```

> Este test es la **garantía ejecutable** del principio №1 de §2.2. Si alguien acopla el dominio a un framework, el CI lo detecta.

---

## 14. Decisiones de diseño (ADR resumidos)

| ADR | Decisión | Razón |
|-----|----------|-------|
| **ADR-001** | Monolito modular por Bounded Context, no microservicios desde el día 1 | Menor complejidad operativa; cada contexto está listo para extraerse (comunicación por puertos) |
| **ADR-002** | Dinero siempre `Decimal`, columnas `NUMERIC(_,2)` | Evitar errores de redondeo de `float`; precisión exacta base 10 |
| **ADR-003** | Cantidades de stock en `Decimal` (no `float`), columna `NUMERIC(_,3)` | El enunciado sugiere `Float`; se prefiere `Decimal` por precisión al acumular movimientos. La fraccionabilidad la decide `UnitOfMeasure.is_fractional`. Si un requisito externo exige `float`, se aísla en infra |
| **ADR-004** | Entidades de dominio ≠ tablas ORM, con mapper explícito | Preservar la regla de dependencia; permitir cambiar ORM/DB sin tocar el core |
| **ADR-005** | Repositorios como `typing.Protocol` (no ABC) | Structural typing: la infra no necesita heredar; menor acoplamiento |
| **ADR-006** | Excepciones de dominio sin HTTP; traducción en handler global | El dominio no conoce el transporte; un solo punto de mapeo a status codes |
| **ADR-007** | Unit of Work para venta + descuento de stock | Atomicidad: nunca venta sin stock descontado ni viceversa |
| **ADR-008** | `reporting` como contexto read-only con read models | Reportar no debe hidratar agregados transaccionales; queries de agregación directas |
| **ADR-009** | Precios congelados (snapshot) en `sale_lines` | Reportes históricos correctos aunque cambien precios de catálogo |
| **ADR-010** | Bruno (`.bru` versionados) como capa E2E de caja negra, **complementaria** al `TestClient` | Suite de contrato/regresión políglota y git-friendly; los agentes IA la editan en texto plano; se ejecuta post-deploy en Harness sin acoplar al runtime Python |

### Control de calidad en el pipeline (Harness + Bruno)

Más allá de los gates de build (lint, type-check, tests, coverage — ver `PLAN`), el pipeline de Harness incorpora un **paso posterior al despliegue** en el entorno de pruebas: ejecuta `bru run` mediante la CLI de Bruno dentro de un contenedor Docker (imagen Node) apuntando con `{{base_url}}` al entorno desplegado. Garantiza que ninguna regresión rompa el **flujo crítico de negocio**:

```
Inventariar  →  Vender  →  Calcular Balance
(POST /products)  (POST /sales)   (GET /reports/balance)
```

Si la colección Bruno falla, el deploy se marca como fallido (gate de regresión).

---

## 15. Roadmap de implementación

> Orden sugerido. Cada fase entrega valor testeable de punta a punta.

1. **Fase 0 — Andamiaje:** estructura de carpetas, `pyproject.toml`, `config.py`, `database.py`, app factory, Alembic inicializado, test de arquitectura (§13.4) en verde.
2. **Fase 1 — `shared/domain`:** `Money`, `Quantity`, `UnitOfMeasure`, `Entity`, `DomainException` + tests unitarios. **Base de todo.**
3. **Fase 2 — `inventory`:** dominio (`Product`, excepciones, repos), infra (modelo, mapper, repo, photo storage), entrypoints + migración. CRUD de productos y ajuste de stock funcionando.
4. **Fase 3 — `sales`:** dominio (`Sale`, `Payment`, `Installment`, `InstallmentCalculator`, `StockPort`), caso de uso `RegisterSaleUseCase` con UoW, adaptador `StockPort`→`inventory`, entrypoints. Registro de venta atómico end-to-end.
5. **Fase 4 — `reporting`:** read models y endpoints de balance/ganancia/cobranzas. Cierra el flujo crítico Inventariar→Vender→Balance, validado por el flow encadenado de Bruno.
6. **Fase 5 — `mobile` (Flet):** cliente HTTP (`httpx`), pantallas de venta, inventario y balances consumiendo `/api`.
7. **Fase 6 — Endurecimiento:** auth, paginación, logging estructurado, observabilidad, y preparación para PostgreSQL.

> **Transversal a todas las fases:** cada endpoint nuevo o modificado lleva su `.bru` equivalente (creado/actualizado por el agente Bruno). Una ruta no se considera terminada hasta que su `.bru` pasa con `bru run` contra la API levantada localmente (ver `PLAN` §"Validación E2E con Bruno").

---

## 16. Glosario del dominio

| Término | Definición |
|---------|------------|
| **Agregado (Aggregate)** | Cluster de entidades tratado como unidad de consistencia. Raíz: `Product`, `Sale` |
| **Value Object** | Objeto inmutable definido por su valor, sin identidad: `Money`, `Quantity`, `Installment` |
| **Puerto (Port)** | Interfaz que el dominio define para hablar con el exterior (repos, storage, otros contextos) |
| **Adaptador (Adapter)** | Implementación concreta de un puerto (SQL repo, local storage) |
| **Bounded Context** | Frontera de modelo con lenguaje y reglas propias: `inventory`, `sales`, `reporting` |
| **Unit of Work** | Patrón que agrupa operaciones de persistencia en una transacción atómica |
| **DTO** | Data Transfer Object: contrato de entrada/salida de la API (Pydantic), nunca lógica de negocio |
| **Snapshot de precio** | Copia del costo/venta congelada en la línea de venta al momento de confirmar |
| **Ganancia bruta** | `Σ (precio_venta − precio_costo) × cantidad` |
| **Ganancia neta** | Ganancia bruta − recargos financieros − gastos operativos |
| **Stock fraccionado** | Cantidad decimal admitida por unidades continuas (`meter`, `kg`) para mercería |

---

*Fin del documento — `docs/PRD-indumentaria-pos.md` · v1.0*
