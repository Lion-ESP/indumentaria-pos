# Backlog · `indumentaria-pos`

> Pendientes posteriores al MVP (Fases 1–4 del [PLAN](./PLAN-desarrollo-y-testing.md) completas: contratos, dominio, infraestructura y frontend Flet).
> Ordenado por prioridad. Cada ítem está redactado como ticket: contexto + criterios de aceptación.

---

## 🔴 Bugs (prioridad alta)

### BUG-1 — No se puede registrar una venta desde la UI Flet ✅ RESUELTO
- **Causa raíz:** la vista de ventas pedía pegar el UUID del producto a mano; vacío/ inválido → `ValueError` → mensaje "revisá el id...". Los productos sí se registran (verificado contra la API). No era un problema de persistencia.
- **Fix (`bugfix/registrar-venta-ui`):** selector de producto poblado desde `GET /products` + botón "Actualizar productos"; tras vender se recarga la lista para reflejar el stock.
- **Criterios de aceptación:**
  - [x] Causa identificada (UI, no cliente ni persistencia).
  - [x] Una venta válida se registra eligiendo el producto de la lista.
  - [x] Feedback claro: "Seleccioná un producto" / "La cantidad y el monto deben ser numéricos".
  - [ ] **Pendiente:** revisión general de layout/diseño de las tres vistas (si persisten detalles visuales, abrir ítem aparte con capturas).

---

## 🟠 Funcionalidad incompleta vs. PRD (RF a medias)

### RF-1.4 — Endpoint de foto de producto
- **Contexto:** `LocalPhotoStorage` (puerto `PhotoStorage`) está implementado pero no hay endpoint que lo use.
- **Criterios de aceptación:**
  - [ ] `POST /products/{id}/photo` (multipart/form-data) que guarda vía `PhotoStorage` y persiste `photo_path`.
  - [ ] `ProductResponse` expone `photo_path`.
  - [ ] Test de integración con `tmp_path`; `.bru` de la subida.

### RF-3.3 — Balance agrupado por producto y por método de pago
- **Contexto:** `SqlBalanceQuery` hoy agrega solo por día/mes.
- **Criterios de aceptación:**
  - [ ] `group_by=product` y `group_by=payment_method` soportados.
  - [ ] Tests de integración por cada dimensión.

### RF-3.4 — Cobranzas futuras (proyección de cuotas)
- **Contexto:** las cuotas se calculan y persisten, pero no hay reporte de cobranza.
- **Criterios de aceptación:**
  - [ ] `GET /reports/receivables?month=YYYY-MM` que proyecta cuotas a cobrar a partir de `Installment.due_date`.
  - [ ] Tests de integración.

### FEAT-cuotas — Exponer cuotas en la respuesta de venta
- **Contexto:** `InstallmentCalculator` genera las cuotas y se persisten, pero `SaleResponse` no las devuelve ni la UI las muestra.
- **Criterios de aceptación:**
  - [ ] `SaleResponse` incluye las cuotas (número, monto, vencimiento) cuando el pago es con tarjeta.
  - [ ] La UI de ventas muestra el detalle de cuotas.

### FEAT-gastos — Ganancia neta real
- **Contexto:** hoy `net_profit == gross_profit` (no hay egresos registrados).
- **Criterios de aceptación:**
  - [ ] Modelo y endpoint para registrar gastos/egresos del período.
  - [ ] `net_profit = gross_profit − gastos` en el balance.

---

## 🟡 Infraestructura de proyecto (documentada, sin materializar)

### INFRA-1 — Crear `.harness/pipeline.yaml`
- **Contexto:** el pipeline está descrito en PLAN §5 y AGENTS.md §4, pero el archivo no existe.
- **Criterios de aceptación:**
  - [ ] Etapa A (build+gates): ruff, mypy, test de arquitectura, pytest, gate global 80%, gate dominio 95% (`coverage report --include="*/domain/*"`).
  - [ ] Etapa B (deploy a test + `bru run` en contenedor Node con `@usebruno/cli`).
  - [ ] El build falla si algún gate o la regresión Bruno fallan.

### INFRA-2 — Migraciones en el flujo de deploy
- **Contexto:** el `lifespan` hace `create_all` (conveniencia de dev); en entornos formales debe gobernar Alembic.
- **Criterios de aceptación:**
  - [ ] Definir/documentar cuándo se corre `alembic upgrade head` en el deploy.
  - [ ] Evaluar quitar `create_all` del `lifespan` en producción (dejarlo solo para dev/test).

---

## 🟢 Endurecimiento (Fase 6 del PRD · post-MVP)

### HARD-1 — Autenticación y autorización
- [ ] Login + protección de endpoints; roles si aplica (operador/admin).

### HARD-2 — Paginación en listados
- [ ] `GET /products` (y futuros listados) con paginación.

### HARD-3 — Observabilidad
- [ ] Logging estructurado y métricas básicas.

### HARD-4 — Migración a PostgreSQL
- **Contexto:** el dominio está desacoplado del motor; el cambio se concentra en la cadena de conexión y revisar `render_as_batch` de Alembic.
- **Criterios de aceptación:**
  - [ ] La suite (unit + integración + e2e) pasa contra PostgreSQL.
  - [ ] Migraciones Alembic aplicables en PostgreSQL.

---

*Mantenimiento: al tomar un ítem, mover su detalle al ticket correspondiente y marcar aquí el avance. Al cerrar, tildar los criterios de aceptación.*
