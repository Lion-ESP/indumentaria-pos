# AGENTS.md — Ecosistema de Desarrollo de IA e Instrucciones del Sistema

Este documento define las reglas de diseño, flujos de trabajo y estándares técnicos que cualquier Agente de IA (Claude Code, Aider, OpenAI Assistants, etc.) debe seguir estrictamente al interactuar con el repositorio `indumentaria-pos`.

> **Documentos de referencia:** [`docs/PRD-indumentaria-pos.md`](./docs/PRD-indumentaria-pos.md) (arquitectura y requerimientos) · [`docs/PLAN-desarrollo-y-testing.md`](./docs/PLAN-desarrollo-y-testing.md) (plan de fases, testing y coverage).

---

## 1. Reglas de Oro de la Arquitectura (DDD / Hexagonal)

NUNCA rompas los límites de las capas bajo ninguna circunstancia. Antes de escribir código, valida estas restricciones:

* **Dominio Puro (`api/app/<contexto>/domain/`):** Solo Python nativo. Queda estrictamente PROHIBIDO importar `fastapi`, `pydantic`, `sqlalchemy`, `sqlmodel` o librerías de terceros dentro de esta carpeta. Toda la lógica de negocio (cuotas, stock decimal, balances) vive aquí, en entidades, value objects y servicios de dominio.
* **Aplicación (`api/app/<contexto>/application/`):** Casos de uso que orquestan el dominio y la persistencia (abren transacción, cargan agregados, invocan comportamiento, confirman). NO contienen reglas de negocio ni dependen de Pydantic/ORM; reciben *comandos* (dataclasses puros).
* **Inversión de Dependencias (DIP):** Los servicios del dominio no interactúan con la base de datos directamente. Debes definir un `Protocol` (interface) en el dominio y heredarlo/implementarlo en la capa de adaptadores (`api/app/<contexto>/adapters/`).
* **Contratos API (`api/app/<contexto>/entrypoints/`):** Usá Pydantic **únicamente** para la validación de Requests y Responses (DTOs), en `entrypoints/schemas.py`. El router de FastAPI recibe el DTO, lo mapea a un comando de aplicación, llama al caso de uso y maneja la respuesta. Las excepciones de dominio se traducen a HTTP en un único *exception handler* global.

### Estructura del backend (Modular Monolith por Bounded Context)

```
api/app/
├── main.py · config.py
├── shared/              # Kernel: Money, Quantity, Entity, DomainException, UoW, DB
│   ├── domain/
│   └── adapters/
├── inventory/           # Bounded Context: Inventario
│   ├── domain/          # entidades, VOs, excepciones, Protocols (puertos)
│   ├── application/     # casos de uso (orquestación)
│   ├── adapters/        # SQLModel models, mappers, repositories, photo_storage
│   └── entrypoints/     # schemas.py (Pydantic) + router.py (FastAPI)
├── sales/               # Bounded Context: Ventas (idem capas)
└── reporting/           # Bounded Context: Balances/Reportes (idem capas)
```

**Convención canónica:** paquete raíz **`app`** (imports `app.<contexto>.<capa>`), sin layout `src/`. La capa de infraestructura se llama **`adapters`**. La regla de dependencia apunta siempre hacia adentro: `entrypoints` → `application` → `domain`; `adapters` implementa los `Protocol` del `domain`. Un contexto no importa clases concretas de otro: se comunican vía puertos (`Protocol`).

---

## 2. Flujo de Trabajo Basado en Especificaciones (Spec-Driven)

Cuando se te asigne una tarea de desarrollo, debes ejecutarla en este orden estricto:

1. **Lectura:** Analizá las especificaciones en `docs/PRD-indumentaria-pos.md` y el plan en `docs/PLAN-desarrollo-y-testing.md`.
2. **Diseño del Contrato:** Si la tarea requiere un nuevo endpoint, modificá o creá primero los esquemas de Pydantic en `entrypoints/schemas.py` y la firma de la ruta (mockeada al inicio) en FastAPI.
3. **Escribir Tests de Dominio:** Escribí las pruebas unitarias en `tests/unit/` que validen la lógica de negocio con mocks (`unittest.mock`), sin tocar la base de datos.
4. **Implementar Lógica:** Escribí el código del dominio (`domain/`) y de aplicación (`application/`) necesario para hacer pasar los tests unitarios.
5. **Persistencia e Integración:** Implementá los repositorios en `adapters/` y escribí los tests de integración en `tests/integration/` usando SQLite en memoria (`sqlite:///:memory:`) con fixtures de pytest que crean y destruyen el esquema por test.

---

## 3. Comandos de Verificación Local

Antes de dar por terminada una tarea, debes ejecutar de forma autónoma los siguientes comandos y asegurar su éxito:

```bash
# Posicionarse en la API
cd api

# Suite de testing completa con reporte de cobertura (gate global)
pytest --cov=app tests/ --cov-fail-under=80

# Formato y linting (ruff reemplaza a black + flake8 + isort)
ruff format app/ tests/
ruff check app/ tests/

# Tipado estático
mypy app/
```

Si la tarea tocó endpoints, además se validan los `.bru` contra la API levantada (ver §5):

```bash
# Terminal 1: levantar la API
cd api && uvicorn app.main:app

# Terminal 2: correr la colección Bruno de caja negra
cd tests-e2e && bru run --env local
```

**Regla de coverage del dominio:** si la cobertura de la capa de dominio (`app/*/domain/`, `app/shared/domain/`) es menor al **95%**, debes refactorizar o añadir más casos de prueba antes de finalizar. El gate dominio se valida con un paso scoped:

```bash
pytest tests/unit \
    --cov=app.inventory.domain --cov=app.sales.domain \
    --cov=app.reporting.domain --cov=app.shared.domain \
    --cov-fail-under=95
```

---

## 4. Integración con Harness (CI/CD)

El pipeline de Harness (`.harness/pipeline.yaml`) está configurado para **rechazar** cualquier código que:

* No pase los tests de `pytest`.
* Reduzca el porcentaje de cobertura global acordado (mínimo 80% global, 95% en dominio).
* Contenga errores de tipado estático (`mypy`).
* No cumpla `ruff check` / `ruff format --check`.
* Rompa la regresión E2E de Bruno post-deploy (`bru run` contra el entorno de test; ver §5).

Asegúrate de que todo esté verde **localmente** antes de proponer cambios: los comandos del pipeline son los mismos de la sección §3 (paridad local ↔ CI).

---

## 5. Agente de Automatización E2E (Bruno Specialist)

Rol específico que se activa ante cualquier cambio en la superficie HTTP de la API. Su responsabilidad es mantener la colección Bruno (`tests-e2e/`) como **suite de contrato y regresión de caja negra**, complementaria al `TestClient` de pytest (no la reemplaza).

### Disparador (obligatorio)

**Cada vez que se cree o modifique un endpoint en FastAPI**, este agente debe **generar o actualizar el archivo `.bru` equivalente** en el mismo cambio. Un endpoint nuevo sin su `.bru` se considera incompleto. La ubicación espeja la del router: endpoint de `sales` → `tests-e2e/sales/<accion>.bru`.

### Reglas de los archivos `.bru`

Los `.bru` viven versionados en el repo (texto plano editable por el agente). Cada uno debe incluir asserts que verifiquen:

1. **Status code HTTP correcto** (`200`, `201`, `409`, `422`, ...), tanto el camino feliz como los de error de dominio.
2. **Estructura del JSON de respuesta** que **coincida con el DTO de Pydantic** correspondiente (todas las claves del `*Response`).
3. **Contratos de negocio**, no solo forma. Ejemplos: al registrar una venta, `total == total_paid` y `gross_profit == (precio_venta − precio_costo) × cantidad`; tras vender, el stock disponible disminuye.

### Entornos

Uso **estricto** de variables de entorno de Bruno: toda URL usa `{{base_url}}` (definida en `tests-e2e/environments/local.bru` y `test.bru`). Nunca hardcodear hosts. Cambiar de entorno = cambiar `--env`, no el `.bru`.

### Flujo crítico encadenado

Mantener `tests-e2e/flows/inventariar-vender-balance.bru`, que encadena **Inventariar → Vender → Calcular Balance** pasando datos entre requests con `bru.setVar` (ej. capturar `product_id` de la respuesta del alta y reusarlo en la venta). Es la red de regresión del negocio.

### Ejecución

```bash
cd tests-e2e
bru run --env local                       # colección completa (dev local)
bru run flows --env local                 # solo el flujo crítico
bru run --env test --reporter-junit results.xml   # CI (Harness)
```

> **Plantilla y ejemplos de `.bru`** (asserts, `tests {}` con `expect`, `script:post-response`, encadenado): ver `docs/PLAN-desarrollo-y-testing.md` §3.4.
