# Plan de Desarrollo y Estrategia de Testing · `indumentaria-pos`

> **Tipo de documento:** Plan de Desarrollo Ágil (Spec-Driven) + Estrategia de Testing/Coverage de nivel producción
> **Complementa a:** [`PRD-indumentaria-pos.md`](./PRD-indumentaria-pos.md)
> **Stack de testing:** `pytest` · `pytest-cov` · `unittest.mock` · `fastapi.testclient.TestClient` · `httpx` · SQLite `:memory:`
> **Toolchain de calidad (decidido):** `ruff` (lint + formato) · `mypy` (type-check) · `respx` (mock HTTP, Fase 4) · `Bruno` (E2E de caja negra, `.bru` + `bru run`)
> **Estado:** v1.0 · Guía de ejecución para el equipo

---

## Tabla de contenidos

1. [Enfoque y principios](#1-enfoque-y-principios)
2. [Plan en fases (Spec-Driven)](#2-plan-en-fases-spec-driven)
   - [Fase 1 — Contratos OpenAPI + mocks](#fase-1--contratos-openapi--rutas-mockeadas)
   - [Fase 2 — Dominio puro + tests unitarios](#fase-2--dominio-puro--tests-unitarios)
   - [Fase 3 — Infraestructura + tests de integración](#fase-3--infraestructura--tests-de-integración)
   - [Fase 4 — Frontend Flet](#fase-4--frontend-flet-consumiendo-la-api)
3. [Estrategia de testing detallada](#3-estrategia-de-testing-detallada)
   - [Pirámide y distribución](#31-pirámide-de-tests-y-distribución-objetivo)
   - [Tests unitarios (dominio aislado)](#32-tests-unitarios--dominio-aislado-con-mock)
   - [Tests de integración (TestClient + SQLite memoria)](#33-tests-de-integración--testclient--sqlite-en-memoria)
   - [E2E de caja negra con Bruno](#34-e2e-de-caja-negra-con-bruno)
4. [Criterios de calidad y coverage](#4-criterios-de-calidad-y-coverage)
   - [Configuración pytest-cov](#41-configuración-de-pytest-cov)
   - [Umbrales obligatorios](#42-umbrales-de-cobertura-obligatorios)
   - [Definition of Done técnico](#43-definition-of-done--listo-para-producción)
5. [CI/CD y gates de calidad (Harness)](#5-cicd-y-gates-de-calidad-harness)
6. [Matriz de trazabilidad RF → tests](#6-matriz-de-trazabilidad-rf--tests)

---

## 1. Enfoque y principios

El desarrollo sigue un enfoque **Spec-Driven**: el **contrato de la API (OpenAPI) es el artefacto que habilita el paralelismo**. Una vez congelado el contrato en la Fase 1, dos corrientes de trabajo avanzan en paralelo:

```
                 ┌─────────────────────────────────────────────┐
 FASE 1          │   Contrato OpenAPI + rutas mockeadas (FastAPI) │
 (contrato)      └───────────────┬─────────────────┬─────────────┘
                                 │                 │
                ┌────────────────▼───┐   ┌─────────▼──────────────────┐
 PARALELO       │ Backend (Fases 2-3)│   │ Frontend Flet (Fase 4)     │
                │ dominio + infra    │   │ consume el mock, luego real│
                └────────────────────┘   └────────────────────────────┘
```

### Principios rectores

1. **El contrato no se rompe sin acuerdo.** Cambiar un schema Pydantic público obliga a versionar o comunicar. El OpenAPI generado es la fuente de verdad del frontend.
2. **Outside-in en el contrato, inside-out en la implementación.** Primero se define la frontera (DTOs/rutas); luego se construye desde el dominio hacia afuera (dominio → infra → wiring).
3. **Tests como red de seguridad de la regla de dependencia.** El dominio se testea sin I/O; si un test de dominio necesita una DB, el diseño está mal.
4. **Coverage es un piso, no una meta.** 95% en dominio / 80% global son condiciones necesarias, no suficientes: cubrir líneas no garantiza cubrir comportamiento. Los criterios de aceptación funcional mandan.

### 1.1 Toolchain de calidad (decidido)

Set único y moderno, configurado en su totalidad desde `pyproject.toml`. Decisión cerrada — no se evalúan alternativas salvo nueva necesidad.

| Necesidad | Herramienta | Reemplaza a | Desde |
|-----------|-------------|-------------|-------|
| Lint + formato de código | **`ruff`** (incluye `ruff format`) | `flake8`, `isort`, `pylint`, `black` | Fase 0 |
| Type-checking estático | **`mypy`** | — | Fase 0 |
| Tests + cobertura | **`pytest` + `pytest-cov`** | `unittest` (runner) | Fase 0 |
| Mock de HTTP en tests | **`respx`** | `httpx.MockTransport` (manual) | Fase 4 |
| E2E de caja negra / regresión | **`Bruno`** (`@usebruno/cli`) | Postman/Newman | Fase 1+ (transversal) |

- **`ruff`** unifica linting y formato en una sola herramienta (Rust, muy rápida). Una dependencia, una config. `ruff format` produce el mismo resultado que `black`.
- **`mypy`** verifica los tipos antes de ejecutar; clave para el dominio (`Decimal` vs `float`, unidades de `Quantity`, contratos de los puertos `Protocol`).
- **`respx`** intercepta las llamadas `httpx` del `api_client` de Flet sin levantar el backend real (aplica recién en Fase 4).
- **`Bruno`** es un cliente de API open-source cuyas colecciones son archivos `.bru` en texto plano versionados en el repo (los edita tanto un humano como un agente IA). Su CLI `bru run` ejecuta la colección contra una API **corriendo**. Complementa al `TestClient` (no lo reemplaza): valida contrato y flujo crítico de caja negra, en dev local y como gate de regresión post-deploy. **Dependencia externa:** requiere Node.js para la CLI (solo en dev/CI, no en el runtime de la app, que sigue siendo Python puro).

---

## 2. Plan en fases (Spec-Driven)

### Fase 1 — Contratos OpenAPI + rutas mockeadas

**Objetivo:** publicar un contrato estable y una API "vacía" navegable, para desbloquear al frontend de inmediato.

**Entregables:**

| # | Entregable | Detalle |
|---|-----------|---------|
| 1.1 | Esquemas Pydantic completos | `CreateProductRequest`, `ProductResponse`, `RegisterSaleRequest`, `SaleResponse`, `BalanceResponse`, `ErrorResponse` (con `code`/`message`) |
| 1.2 | Rutas mockeadas en FastAPI | Cada endpoint del PRD declarado con `response_model` y datos de ejemplo *hardcodeados* (sin dominio ni DB) |
| 1.3 | Contrato de errores | Schema único de error alineado con el handler global del PRD (§9): `{ "error": { "code": ..., "message": ... } }` |
| 1.4 | OpenAPI exportado | `GET /openapi.json` y Swagger UI funcionando; export del JSON versionado en `docs/openapi/openapi.v1.json` |
| 1.5 | Ejemplos en los schemas | `model_config = {"json_schema_extra": {"examples": [...]}}` para que el frontend tenga payloads reales |

**Ejemplo de ruta mockeada:**

```python
# sales/entrypoints/router.py  (FASE 1 — mock)
from fastapi import APIRouter, status
from decimal import Decimal
from uuid import uuid4
from app.sales.entrypoints.schemas import RegisterSaleRequest, SaleResponse

router = APIRouter(prefix="/sales", tags=["sales"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SaleResponse)
def register_sale(body: RegisterSaleRequest) -> SaleResponse:
    # MOCK: respuesta determinística para desbloquear al frontend.
    return SaleResponse(
        id=uuid4(),
        total=Decimal("17000.00"),
        total_paid=Decimal("17000.00"),
        gross_profit=Decimal("6800.00"),
    )
```

**Tests de Fase 1 (contract tests):**
- El OpenAPI generado contiene todas las rutas y schemas esperados.
- Cada mock responde con un payload que **valida contra su `response_model`** (lo garantiza FastAPI, pero se testea el status code y la forma).
- Snapshot del `openapi.json`: un test falla si el contrato cambia sin actualizar el snapshot (detección de cambios no intencionados).

```python
def test_openapi_contiene_endpoints_del_contrato(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/sales" in paths
    assert "/products" in paths
    assert "post" in paths["/sales"]

def test_mock_register_sale_cumple_response_model(client):
    payload = {
        "lines": [{"product_id": str(uuid4()), "quantity": "2"}],
        "payments": [{"method": "cash", "amount": "17000.00"}],
    }
    resp = client.post("/sales", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert {"id", "total", "total_paid", "gross_profit"} <= body.keys()
```

**Validación E2E con Bruno (Fase 1):** se inicializa la colección `tests-e2e/` (`bruno.json` + `environments/local.bru`). Por cada ruta mockeada se crea su `.bru` con asserts de **status code** y **forma del JSON** (claves del DTO). Contra el mock, los asserts de contrato ya deben pasar (`bru run --env local`); los asserts de contrato de negocio quedan marcados como pendientes hasta la Fase 3.

**Criterio de salida de Fase 1:** Swagger UI navegable, `openapi.v1.json` versionado, contract tests en verde, **colección Bruno inicializada y verde contra el mock**. **El frontend puede arrancar.**

---

### Fase 2 — Dominio puro + tests unitarios

**Objetivo:** implementar el corazón de negocio (capas `shared/domain`, `*/domain`, `*/application`) **sin tocar DB ni framework**, con cobertura ≥ 95%.

**Entregables:**

| # | Entregable | Tests asociados |
|---|-----------|-----------------|
| 2.1 | Value Objects `Money`, `Quantity`, `UnitOfMeasure` | redondeo, fraccionabilidad, operaciones, inmutabilidad |
| 2.2 | Entidades `Product`, `Sale`, `SaleLine`, `Payment`, `Installment` | invariantes, propiedades calculadas (`total`, `gross_profit`) |
| 2.3 | Servicios de dominio `InstallmentCalculator` | descomposición de cuotas y redondeo en la última |
| 2.4 | Excepciones de dominio | se lanzan en las condiciones correctas |
| 2.5 | Casos de uso (`RegisterSaleUseCase`, `CreateProduct`, etc.) | orquestación con **mocks** de repos/puertos |

**Regla:** los tests de esta fase **no importan SQLAlchemy, FastAPI ni abren conexiones**. Los puertos (`StockPort`, `SaleRepository`, `PhotoStorage`) se sustituyen por `unittest.mock` o dobles en memoria.

**Validación E2E con Bruno (Fase 2):** N/A directo — esta fase no expone endpoints (es dominio puro). La lógica de cálculo (cuotas, totales, ganancia) que aquí se valida con tests unitarios se reconfirma de extremo a extremo en los asserts de **contrato de negocio** de los `.bru` cuando los endpoints se vuelven funcionales (Fase 3).

**Criterio de salida de Fase 2:** cobertura de `*/domain` y `*/application` ≥ 95%; todos los RF de cálculo (cuotas, balances, validación de venta) verificados con tests unitarios. Mocks ya conectados a los casos de uso muestran que el contrato de puertos es correcto.

---

### Fase 3 — Infraestructura + tests de integración

**Objetivo:** reemplazar los mocks de las rutas por los casos de uso reales, implementar repos SQLModel, mappers, UoW, Alembic y almacenamiento de fotos. Los endpoints pasan de *mockeados* a *funcionales*.

**Entregables:**

| # | Entregable | Tests asociados |
|---|-----------|-----------------|
| 3.1 | Modelos SQLModel + mappers ORM↔dominio | round-trip preserva precisión `Decimal` |
| 3.2 | Repositorios SQL (`SqlProductRepository`, `SqlSaleRepository`) | CRUD contra SQLite `:memory:` |
| 3.3 | Unit of Work | commit/rollback atómico; venta + descuento de stock todo-o-nada |
| 3.4 | Adaptador `StockPort` → `inventory` | cruce entre contextos funciona |
| 3.5 | Migraciones Alembic | `upgrade head` parte de DB vacía sin error; `render_as_batch` en SQLite |
| 3.6 | `LocalPhotoStorage` | guardado/borrado en `tmp_path` |
| 3.7 | Wiring real (`Depends`) reemplaza mocks de Fase 1 | endpoints reales |

**Validación E2E con Bruno (Fase 3):** cada `.bru` pasa de mock a API real. Se completan los asserts de **contrato de negocio** (ej. `total == total_paid`, `gross_profit == (venta−costo)×cant`, stock restante tras la venta) y los de **error** (409 stock insuficiente, 422 venta no cuadra). Se implementa el flow encadenado `flows/inventariar-vender-balance.bru` (crea producto → captura `product_id` con `bru.setVar` → registra venta → consulta balance). Una ruta **no está terminada** hasta que su `.bru` pasa con `bru run --env local` contra la API levantada (`uvicorn`).

**Criterio de salida de Fase 3:** tests de integración con `TestClient` cubren los flujos completos (alta producto → venta → descuento stock → balance) contra SQLite en memoria; cobertura global ≥ 80%; las rutas devuelven datos reales y los errores de dominio se traducen a HTTP correctos (404/409/422); **toda la colección Bruno verde con `bru run` contra la API local**.

---

### Fase 4 — Frontend Flet consumiendo la API

**Objetivo:** la app Flet (`/mobile`) consume primero el mock (disponible desde Fase 1) y migra a la API real cuando la Fase 3 cierra.

**Entregables:**

| # | Entregable | Detalle |
|---|-----------|---------|
| 4.1 | Cliente HTTP (`api_client/`) con `httpx` | tipado contra los DTOs del contrato; manejo de `ErrorResponse` por `code` |
| 4.2 | Vistas: venta, inventario, balances | consumen endpoints reales |
| 4.3 | Manejo de errores de negocio en UI | mapea `code` (`insufficient_stock`, `payments_do_not_match_total`) a mensajes de usuario |
| 4.4 | Tests del cliente HTTP | con `httpx.MockTransport` o `respx`, sin levantar la API real |

**Estrategia de testing del frontend:** el `api_client` se testea aislando el transporte HTTP con **`respx`**, verificando que serializa requests y deserializa responses/errores según el contrato. La lógica de presentación (state) se testea con dobles del cliente. **No se requiere E2E de UI Flet para el gate de coverage del backend**, pero se recomienda un smoke test manual del flujo de venta.

**Validación E2E con Bruno (Fase 4):** el `api_client` de Flet y la colección Bruno consumen **el mismo contrato**, así que los `.bru` actúan de oráculo: si `bru run` pasa contra la API, el cliente Flet tiene un backend confiable. Al cerrar un endpoint o cambiar un DTO, se actualiza el `.bru` correspondiente antes de tocar el cliente Flet.

---

## 3. Estrategia de testing detallada

### 3.1 Pirámide de tests y distribución objetivo

```
          ▔▔▔▔          E2E caja negra (Bruno)          fuera de la pirámide:
        ╱      ╲        regresión post-deploy,           API real, no cuenta coverage
       ╱  Bruno ╲       flujo crítico de negocio
      ╱──────────╲
            ╱╲          E2E / API in-process            ~15%   flujos completos
           ╱  ╲         (TestClient)                            sin servidor
          ╱────╲
         ╱      ╲       Integración (repos, mappers,   ~25%   DB en memoria
        ╱        ╲      UoW, Alembic)
       ╱──────────╲
      ╱            ╲    Unitarios (dominio, casos      ~60%   sin I/O, milisegundos
     ╱              ╲   de uso con mocks)
    ╱────────────────╲
```

| Tipo | Carpeta | Velocidad | Toca DB | Toca HTTP | Coverage |
|------|---------|-----------|---------|-----------|----------|
| Unitario | `api/tests/unit/` | < 1 ms/test | ❌ | ❌ | sí |
| Integración | `api/tests/integration/` | ~10-50 ms/test | ✅ SQLite `:memory:` | parcial | sí |
| E2E/API in-process | `api/tests/e2e/` | ~50-200 ms/test | ✅ | ✅ `TestClient` | sí |
| E2E caja negra | `tests-e2e/` (Bruno) | servidor + red | ✅ entorno real | ✅ HTTP real | no |

> **Bruno está "fuera" de la pirámide de coverage** a propósito: no ejecuta código Python en proceso, sino que golpea la API por HTTP como un cliente externo. Su valor no es cubrir líneas, sino **garantizar el contrato y el flujo de negocio** contra un despliegue real (dev local y CI post-deploy).

### 3.2 Tests unitarios — dominio aislado con `mock`

**Objetivo:** verificar reglas de negocio puras sin ninguna dependencia externa. Los puertos se sustituyen por dobles.

#### Caso 1 — Cálculo de cuotas (regla crítica)

```python
# tests/unit/sales/test_installment_calculator.py
from datetime import date
from decimal import Decimal
import pytest
from app.sales.domain.entities import Payment, PaymentMethod
from app.sales.domain.services import InstallmentCalculator
from app.shared.domain.money import Money
from app.sales.domain.exceptions import CuotasInvalidasException

class TestInstallmentCalculator:
    def test_tres_cuotas_la_ultima_absorbe_el_redondeo(self):
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("100.00")),
                          installments_count=3)
        cuotas = InstallmentCalculator().build(payment, date(2026, 1, 1))
        montos = [c.amount.amount for c in cuotas]
        assert montos == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        assert sum(montos) == Decimal("100.00")

    def test_aplica_recargo_financiero(self):
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("100.00")),
                          installments_count=2, surcharge_rate=Decimal("0.20"))
        cuotas = InstallmentCalculator().build(payment, date(2026, 1, 1))
        assert sum(c.amount.amount for c in cuotas) == Decimal("120.00")

    def test_vencimientos_mensuales_consecutivos(self):
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("90.00")),
                          installments_count=3)
        cuotas = InstallmentCalculator().build(payment, date(2026, 1, 15))
        assert [c.due_date for c in cuotas] == [
            date(2026, 1, 15), date(2026, 2, 15), date(2026, 3, 15)]

    def test_pago_no_tarjeta_no_genera_cuotas(self):
        payment = Payment(PaymentMethod.CASH, Money(Decimal("100.00")))
        assert InstallmentCalculator().build(payment, date(2026, 1, 1)) == []

    def test_cuotas_menor_a_uno_lanza_excepcion(self):
        payment = Payment(PaymentMethod.CREDIT_CARD, Money(Decimal("100.00")),
                          installments_count=0)
        with pytest.raises(CuotasInvalidasException):
            InstallmentCalculator().build(payment, date(2026, 1, 1))
```

#### Caso 2 — Caso de uso con puertos mockeados (sin DB)

```python
# tests/unit/sales/test_register_sale_use_case.py
from decimal import Decimal
from unittest.mock import MagicMock, call
from uuid import uuid4
import pytest
from app.sales.application.use_cases import (
    RegisterSaleUseCase, RegisterSaleCommand, LineCommand, PaymentCommand)
from app.sales.domain.services import InstallmentCalculator
from app.sales.domain.exceptions import VentaNoCuadraException
from app.inventory.domain.exceptions import StockInsuficienteException
from app.shared.domain.money import Money

@pytest.fixture
def stock_port():
    port = MagicMock()
    port.get_pricing.return_value = (Money(Decimal("100.00")), Money(Decimal("60.00")))
    return port

@pytest.fixture
def uow():
    """UoW falso: context manager que registra commits sin tocar DB."""
    fake = MagicMock()
    fake.__enter__.return_value = fake
    fake.__exit__.return_value = False
    return fake

class TestRegisterSaleUseCase:
    def test_venta_valida_descuenta_stock_y_commitea(self, uow, stock_port):
        product_id = uuid4()
        uc = RegisterSaleUseCase(uow, stock_port, InstallmentCalculator())
        cmd = RegisterSaleCommand(
            lines=[LineCommand(product_id, Decimal("2"))],
            payments=[PaymentCommand("cash", Decimal("200.00"))],
        )
        sale_id = uc.execute(cmd)
        assert sale_id is not None
        stock_port.decrease_stock.assert_called_once()
        uow.commit.assert_called_once()

    def test_venta_que_no_cuadra_no_descuenta_stock(self, uow, stock_port):
        uc = RegisterSaleUseCase(uow, stock_port, InstallmentCalculator())
        cmd = RegisterSaleCommand(
            lines=[LineCommand(uuid4(), Decimal("2"))],   # total 200
            payments=[PaymentCommand("cash", Decimal("150.00"))],  # paga 150
        )
        with pytest.raises(VentaNoCuadraException):
            uc.execute(cmd)
        stock_port.decrease_stock.assert_not_called()
        uow.commit.assert_not_called()

    def test_propaga_stock_insuficiente(self, uow, stock_port):
        stock_port.decrease_stock.side_effect = StockInsuficienteException("SKU", 5, 2)
        uc = RegisterSaleUseCase(uow, stock_port, InstallmentCalculator())
        cmd = RegisterSaleCommand(
            lines=[LineCommand(uuid4(), Decimal("2"))],
            payments=[PaymentCommand("cash", Decimal("200.00"))],
        )
        with pytest.raises(StockInsuficienteException):
            uc.execute(cmd)
        uow.commit.assert_not_called()
```

> **Patrón clave:** el caso de uso se prueba con `MagicMock` para `StockPort` y `UnitOfWork`. Esto verifica la **orquestación** (qué se llama, en qué orden, qué se commitea) sin necesidad de DB. Las reglas de negocio puras (cuándo lanzar `VentaNoCuadra`) viven en la entidad y se testean directamente sobre ella.

### 3.3 Tests de integración — `TestClient` + SQLite en memoria

**Objetivo:** verificar que las capas reales (router → caso de uso → repo SQL → DB) funcionan juntas, con una DB efímera que se crea y destruye por test/sesión.

#### Fixtures de pytest (conftest)

```python
# tests/integration/conftest.py
import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import create_app
from app.shared.adapters.database import get_session  # dependency a sobreescribir

@pytest.fixture(name="engine")
def engine_fixture():
    """Engine SQLite en memoria compartido entre conexiones del mismo test.
    StaticPool + check_same_thread=False: una sola conexión lógica para
    que el TestClient (otro 'thread') vea las mismas tablas."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)   # crea el esquema
    yield engine
    SQLModel.metadata.drop_all(engine)     # destruye al terminar

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(engine):
    """TestClient con la dependency de sesión sobreescrita por la DB en memoria."""
    def _get_session_override():
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_session] = _get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
```

> **Por qué `StaticPool` + `check_same_thread=False`:** `sqlite://` (in-memory) crea una DB por conexión. Sin `StaticPool`, el `TestClient` y el test verían bases distintas (uno con tablas, otro vacío). `StaticPool` fuerza una única conexión reutilizada, de modo que el esquema creado en el fixture es visible para los requests.

> **Aislamiento por test:** el fixture `engine` tiene scope de función (default), así cada test arranca con esquema limpio y se destruye al final. Para suites grandes se puede usar scope de sesión + transacción con rollback por test (más rápido), pero el scope de función es el más simple y seguro como default.

#### Test de integración de un flujo completo

```python
# tests/integration/test_sale_flow.py
from decimal import Decimal

class TestSaleFlow:
    def test_venta_descuenta_stock_y_calcula_ganancia(self, client):
        # 1. Alta de producto con stock inicial
        create = client.post("/products", json={
            "sku": "REM-001", "name": "Remera", "unit": "unit",
            "cost_price": "60.00", "sale_price": "100.00", "initial_stock": "10",
        })
        assert create.status_code == 201
        product_id = create.json()["id"]

        # 2. Registrar venta de 2 unidades
        sale = client.post("/sales", json={
            "lines": [{"product_id": product_id, "quantity": "2"}],
            "payments": [{"method": "cash", "amount": "200.00"}],
        })
        assert sale.status_code == 201
        assert Decimal(sale.json()["gross_profit"]) == Decimal("80.00")  # (100-60)*2

        # 3. El stock quedó en 8
        detail = client.get(f"/products/{product_id}")
        assert Decimal(detail.json()["stock"]) == Decimal("8")

    def test_venta_con_stock_insuficiente_devuelve_409(self, client):
        create = client.post("/products", json={
            "sku": "REM-002", "name": "Remera", "unit": "unit",
            "cost_price": "60.00", "sale_price": "100.00", "initial_stock": "1",
        })
        product_id = create.json()["id"]
        resp = client.post("/sales", json={
            "lines": [{"product_id": product_id, "quantity": "5"}],
            "payments": [{"method": "cash", "amount": "500.00"}],
        })
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "insufficient_stock"

    def test_venta_que_no_cuadra_devuelve_422(self, client):
        create = client.post("/products", json={
            "sku": "REM-003", "name": "Remera", "unit": "unit",
            "cost_price": "60.00", "sale_price": "100.00", "initial_stock": "10",
        })
        product_id = create.json()["id"]
        resp = client.post("/sales", json={
            "lines": [{"product_id": product_id, "quantity": "2"}],
            "payments": [{"method": "cash", "amount": "150.00"}],
        })
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "payments_do_not_match_total"
```

#### Test de integración del repositorio (round-trip de precisión)

```python
# tests/integration/test_product_repository.py
from decimal import Decimal
from app.inventory.adapters.repositories import SqlProductRepository
from app.inventory.domain.entities import Product
from app.shared.domain.money import Money
from app.shared.domain.quantity import Quantity, UnitOfMeasure

def test_round_trip_preserva_fraccion_de_mercería(session):
    repo = SqlProductRepository(session)
    cinta = Product(sku="CINTA-01", name="Cinta", unit=UnitOfMeasure.METER,
                    cost_price=Money(Decimal("120.50")),
                    sale_price=Money(Decimal("200.00")),
                    stock=Quantity(Decimal("2.750"), UnitOfMeasure.METER))
    repo.add(cinta)
    session.commit()

    recuperado = repo.get_by_sku("CINTA-01")
    assert recuperado.stock.value == Decimal("2.750")    # sin pérdida de precisión
    assert recuperado.cost_price.amount == Decimal("120.50")
    assert recuperado.unit == UnitOfMeasure.METER
```

### 3.4 E2E de caja negra con Bruno

**Objetivo:** validar contrato y flujo de negocio contra una API **corriendo** (no in-process), con archivos `.bru` versionados que un agente IA crea y mantiene en texto plano.

#### Estructura de la colección (`tests-e2e/`)

```
tests-e2e/
├── bruno.json                       # { "version": "1", "name": "indumentaria-pos", "type": "collection" }
├── environments/
│   ├── local.bru                    # base_url: http://localhost:8000
│   └── test.bru                     # base_url del entorno de test (Harness)
├── inventory/
│   ├── create-product.bru
│   └── get-product.bru
├── sales/
│   └── register-sale.bru
├── reporting/
│   └── get-balance.bru
└── flows/
    └── inventariar-vender-balance.bru   # flujo crítico encadenado (regresión)
```

#### Entorno con `{{base_url}}` (`environments/local.bru`)

```
vars {
  base_url: http://localhost:8000
}
```

> **Regla estricta:** ninguna URL hardcodeada en los `.bru`. Siempre `{{base_url}}` para apuntar a local (`uvicorn`) o al entorno de test desplegado en Harness, intercambiando solo `--env`.

#### Ejemplo de request con asserts (`sales/register-sale.bru`)

```
meta {
  name: Registrar venta (efectivo)
  type: http
  seq: 1
}

post {
  url: {{base_url}}/sales
  body: json
}

body:json {
  {
    "lines": [{ "product_id": "{{product_id}}", "quantity": "2" }],
    "payments": [{ "method": "cash", "amount": "200.00" }]
  }
}

assert {
  res.status: eq 201
  res.body.total: eq "200.00"
}

tests {
  test("status 201 Created", function () {
    expect(res.getStatus()).to.equal(201);
  });

  test("la respuesta cumple el DTO SaleResponse", function () {
    const body = res.getBody();
    expect(body).to.have.all.keys("id", "total", "total_paid", "gross_profit");
  });

  test("contrato de negocio: la venta cuadra (total == pagado)", function () {
    const body = res.getBody();
    expect(Number(body.total)).to.equal(Number(body.total_paid));
  });

  test("contrato de negocio: ganancia bruta = (venta - costo) x cantidad", function () {
    const body = res.getBody();
    expect(Number(body.gross_profit)).to.equal(80.00); // (100 - 60) * 2
  });
}
```

#### Flujo crítico encadenado (`flows/inventariar-vender-balance.bru`)

El caso de regresión core encadena los tres pasos del negocio, pasando datos entre requests con variables de runtime:

```
// 1) create-product.bru  → post-response: captura el id generado
script:post-response {
  bru.setVar("product_id", res.getBody().id);
}

// 2) register-sale.bru    → usa {{product_id}}; asserta total y gross_profit
// 3) get-balance.bru      → GET {{base_url}}/reports/balance?from=...&to=...
//                           asserta que la ganancia bruta del período incluye la venta
```

#### Ejecución con la CLI (`bru run`)

```bash
# Toda la colección contra el entorno local (API levantada con uvicorn)
cd tests-e2e
bru run --env local

# Solo el flujo crítico de regresión
bru run flows --env local

# En CI: salida JUnit para que Harness publique resultados
bru run --env test --reporter-junit results.xml
```

> **Requisito:** la API debe estar **corriendo** antes de `bru run` (en local: `uvicorn app.main:app`; en CI: tras el deploy al entorno de test). La CLI de Bruno se instala con `npm install -g @usebruno/cli` (o `npx @usebruno/cli`), por lo que el runner necesita Node.js.

---

## 4. Criterios de calidad y coverage

### 4.1 Configuración de `pytest-cov`

**`api/pyproject.toml`:**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]                 # 'app' importable desde api/ (sin layout src/)
addopts = """
    --strict-markers
    --cov=app
    --cov-report=term-missing
    --cov-report=html:coverage_html
    --cov-report=xml:coverage.xml
    --cov-fail-under=80
"""
markers = [
    "unit: tests unitarios de dominio sin I/O",
    "integration: tests con DB SQLite en memoria",
    "e2e: tests de API completos con TestClient",
]

[tool.coverage.run]
branch = true                      # cobertura de ramas, no solo líneas
source = ["app"]
omit = [
    "*/entrypoints/schemas.py",    # DTOs declarativos (los valida Pydantic)
    "*/adapters/models.py",  # tablas declarativas (sin lógica)
    "*/__init__.py",
    "*/main.py",                   # wiring, cubierto por e2e
]

[tool.coverage.report]
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
    "\\.\\.\\.",                  # cuerpos de Protocol (...)
    "if __name__ == .__main__.:",
]
```

> **`branch = true` es obligatorio:** la cobertura de líneas miente. Un `if x: ...` con cobertura de línea al 100% puede no haber ejecutado nunca la rama `else`. La cobertura de ramas exige recorrer ambos caminos — esencial para reglas de negocio con condiciones (stock suficiente/insuficiente, venta cuadra/no cuadra).

### 4.2 Umbrales de cobertura obligatorios

| Capa / Paquete | Umbral mínimo | Justificación |
|----------------|---------------|---------------|
| **Dominio** (`*/domain/`, `shared/domain/`) | **95%** (líneas **y** ramas) | Es el activo de negocio; barato de testear (sin I/O); cada regla debe estar cubierta |
| **Aplicación** (`*/application/`) | **90%** | Orquestación crítica (atomicidad de ventas); se testea con mocks |
| **Global del proyecto** | **80%** | Piso de calidad para toda la base |
| Adaptadores (`*/adapters/`) | ~75% (sin gate duro) | Cubierta principalmente por integración; mappers y repos sí, no se exige cubrir cada branch defensivo |
| Entrypoints (`*/entrypoints/`) | cubierta por e2e | Los routers se ejercitan vía `TestClient` |

**Gate por capa (más estricto que el global).** `--cov-fail-under=80` solo cubre el global. Para forzar el **95% en dominio** se reutiliza el `.coverage` de la corrida completa y se filtra el reporte a las capas de dominio:

```bash
# Gate 1 — global 80% (produce .coverage con source=app)
pytest --cov=app --cov-fail-under=80

# Gate 2 — dominio 95%: filtra el .coverage existente a las capas domain.
coverage report --include="*/domain/*" --fail-under=95
```

> **Por qué `--include` y no `--cov=app.<ctx>.domain`:** con `source = ["app"]` en `pyproject.toml`, pasar `--cov=app.inventory.domain` igual mide *toda* la app (la unión con `source`), arrastrando el porcentaje hacia abajo cuando existen adapters/entrypoints no cubiertos por los unitarios. `coverage report --include="*/domain/*"` filtra el dato ya recolectado a los módulos de dominio y aplica el umbral solo sobre ellos.

### 4.3 Definition of Done — "Listo para Producción"

Un módulo/Bounded Context se considera **Listo para Producción** solo si cumple **todos** estos criterios técnicos:

**Cobertura y testing**
- [ ] Cobertura de dominio ≥ 95% (líneas y ramas); global del módulo ≥ 80%.
- [ ] Cada RF del módulo tiene al menos un test que lo verifica (ver matriz §6).
- [ ] Casos límite cubiertos: cero, negativos, fracción en unidad discreta, redondeo de cuotas, stock exacto/insuficiente, venta que no cuadra.
- [ ] Tests unitarios del dominio **no importan** `fastapi`/`sqlalchemy`/`sqlmodel` (test de arquitectura del PRD §13.4 en verde).
- [ ] Tests de integración corren contra SQLite `:memory:` y son **independientes del orden** (sin estado compartido entre tests).

**Contrato y errores**
- [ ] Endpoints alineados con el `openapi.v1.json` versionado; cambios de contrato comunicados.
- [ ] Toda excepción de dominio del módulo se traduce al status HTTP correcto (404/409/422) y el `code` del error está documentado.
- [ ] Validación de entrada por Pydantic cubre tipos, rangos y formatos (`ge`, `gt`, `pattern`, `decimal_places`).
- [ ] Cada endpoint del módulo tiene su `.bru` equivalente en `tests-e2e/` (status + estructura del DTO + contrato de negocio) y la colección pasa con `bru run` contra la API local.

**Calidad de código**
- [ ] Type-check sin errores (`mypy`).
- [ ] Linter y formato en verde (`ruff check` + `ruff format --check`).
- [ ] Cero `print`/`TODO`/`FIXME` sin ticket asociado.
- [ ] Migración Alembic aplicable desde DB vacía (`upgrade head`) y reversible si aplica.

**Integridad funcional**
- [ ] Operaciones que mutan stock + venta son atómicas (verificado con un test de rollback).
- [ ] Precisión `Decimal` preservada en round-trip DB (sin conversión a `float`).
- [ ] Documentación mínima: docstring en casos de uso y entradas en el changelog si aplica.

> **Regla de oro del DoD:** "verde en CI" incluye los **dos gates de coverage** (global 80% + dominio 95%) y el test de arquitectura. Si alguno falla, el módulo **no** está listo, sin excepción.

---

## 5. CI/CD y gates de calidad (Harness)

El pipeline vive en `.harness/pipeline.yaml` y **rechaza** todo cambio que: (1) no pase `pytest`, (2) reduzca la cobertura global acordada, (3) tenga errores de tipado estático (`mypy`), o (4) rompa la regresión E2E de Bruno post-deploy. Se ejecuta en dos etapas.

**Etapa A — Build & gates (sobre el código, *fail-fast*):**

```
1. lint + format check      (ruff check, ruff format --check)  → rápido, falla primero
2. type-check               (mypy app)
3. test de arquitectura     (dominio sin frameworks)
4. tests unitarios          (pytest tests/unit)          → milisegundos
5. gate dominio 95%         (coverage report --include="*/domain/*" --fail-under=95)
6. tests integración + e2e  (pytest tests/integration tests/e2e)
7. gate global 80%          (--cov-fail-under=80)
8. publicar coverage.xml / html  (artefacto del build)
```

**Etapa B — Deploy a test + regresión E2E (Bruno):**

```
9.  deploy de la API al entorno de test
10. bru run en contenedor Docker (imagen Node con @usebruno/cli):
      bru run --env test --reporter-junit results.xml
      apunta {{base_url}} al entorno desplegado
11. publicar results.xml (resultados E2E) como artefacto
```

Paso de Harness (esquema):

```yaml
# .harness/pipeline.yaml (fragmento de la etapa B)
- step:
    name: E2E Regression (Bruno)
    type: Run
    spec:
      connectorRef: docker_hub
      image: node:20-alpine
      command: |
        npm install -g @usebruno/cli
        cd tests-e2e
        bru run --env test --reporter-junit results.xml
```

> Si la colección Bruno falla en el paso 10, el despliegue se marca como fallido: una regresión en el flujo **Inventariar → Vender → Calcular Balance** bloquea la promoción del entorno.

**Principios del pipeline:**
- **Fail-fast:** lo barato y de alto valor (lint, type-check, unit) corre primero. No se gasta tiempo en integración si el dominio está roto.
- **Gates duros:** los pasos 1, 2, 3, 5, 7 y 10 **bloquean el merge / la promoción**. No son advertencias.
- **Dos naturalezas de E2E:** el paso 6 (TestClient in-process) corre sin servidor y cuenta coverage; el paso 10 (Bruno) corre contra el deploy real y no cuenta coverage — es la red de regresión de caja negra.
- **Coverage como artefacto:** el reporte HTML se publica para inspección, pero el gate es automático (no depende de revisión humana).
- **Paridad local↔CI:** los comandos del pipeline son los mismos del AGENTS.md §3, para que "verde en local" implique "verde en Harness".

---

## 6. Matriz de trazabilidad RF → tests

Garantiza que cada requerimiento funcional del PRD tiene cobertura explícita.

| RF (PRD) | Descripción | Tipo de test | Test(s) representativo(s) |
|----------|-------------|--------------|---------------------------|
| RF-1.2 | Stock fraccionado en `meter`/`kg` | Unit + Integración | `test_metro_admite_fraccion`, `test_round_trip_preserva_fraccion_de_mercería` |
| RF-1.2 | Rechazo de fracción en `unit` | Unit | `test_unidad_discreta_rechaza_fraccion` |
| RF-1.3 | Ajuste de stock sin negativo | Unit | `test_decrease_stock_insuficiente_lanza` |
| RF-1.4 | Foto de producto | Integración | `test_local_photo_storage_guarda_y_borra` (`tmp_path`) |
| RF-2.3 | La venta debe cuadrar | Unit + E2E | `test_venta_que_no_cuadra_*` |
| RF-2.4 | Descomposición de cuotas + redondeo | Unit | `test_tres_cuotas_la_ultima_absorbe_el_redondeo` |
| RF-2.5 | Recargo financiero | Unit | `test_aplica_recargo_financiero` |
| RF-2.6 | Descuento de stock atómico | Unit + Integración | `test_propaga_stock_insuficiente`, `test_rollback_no_persiste_venta` |
| RF-2.7 | Stock insuficiente → 409 | E2E | `test_venta_con_stock_insuficiente_devuelve_409` |
| RF-3.1 | Ganancia bruta por período | Unit + E2E | `test_gross_profit_*`, `test_venta_descuenta_stock_y_calcula_ganancia` |
| RF-3.3 | Agregación por dimensión | Integración | `test_balance_group_by_day`, `test_profit_group_by_product` |
| RF-3.4 | Cobranza futura (cuotas) | Integración | `test_receivables_por_mes` |

**Cobertura E2E de caja negra (Bruno) — contrato + flujo de negocio contra API real:**

| RF (PRD) | Descripción | Archivo `.bru` | Asserts clave |
|----------|-------------|----------------|---------------|
| RF-1.1 | Alta de producto | `inventory/create-product.bru` | 201 + claves de `ProductResponse` |
| RF-2.3 | La venta cuadra | `sales/register-sale.bru` | `total == total_paid` |
| RF-3.1 | Ganancia bruta | `sales/register-sale.bru` | `gross_profit == (venta−costo)×cant` |
| RF-2.7 | Stock insuficiente → 409 | `sales/register-sale.bru` (caso negativo) | `res.status: eq 409`, `code: insufficient_stock` |
| Flujo crítico | Inventariar→Vender→Balance | `flows/inventariar-vender-balance.bru` | encadenado con `bru.setVar`; balance refleja la venta |

> **Mantenimiento de la matriz:** cada nuevo RF entra con su fila aquí antes de cerrar el ticket. Un RF sin fila = RF sin cobertura garantizada = no pasa el DoD. Los endpoints, además, suman su fila en la tabla Bruno.

---

*Fin del documento — `docs/PLAN-desarrollo-y-testing.md` · v1.0*
