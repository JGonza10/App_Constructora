# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

Aplicación web Python/Flask (monolítica, sin frontend separado) para administrar la operación de una empresa constructora. Todo el dominio, rutas y mensajes están en español — sigue esa convención.

**Reescrita por completo el 2026-08-21** — la versión anterior era Node.js/Express + React (ver historial de git antes de ese commit si necesitas referencia). Se reescribió porque el modelo de datos anterior era incoherente: exigía capturar el monto final del contrato de una obra *antes* de que existiera ninguna cotización, y `Presupuesto`/`Obra.monto_contrato` eran dos números que nunca se sincronizaban entre sí.

## El flujo que gobierna todo el diseño

```
Cliente → Levantamiento (qué pidió el cliente) → Cotización (versionable, línea por línea)
   → [al ACEPTARSE] nace la Obra, con monto_contrato = total de esa cotización
      → gastos, mano_obra, avance, tareas, bitácora, documentos, pagos_cliente,
        todo con obra_id como llave — nunca se mezclan entre obras
```

No existe una ruta para crear una `Obra` directamente — la única forma de que exista es `cotizaciones.aceptar()` (`constructora/cotizaciones.py`). Si necesitas agregar una obra "manual" para algún caso especial, resiste la tentación de agregar un formulario directo: crea el levantamiento + cotización aceptada por el mismo camino, o vas a reintroducir la misma incoherencia que motivó la reescritura.

Cada vista de creación, al guardar, redirige a una pantalla de "¿qué sigue?" (`obras/siguiente_registro.html`, `levantamientos/siguiente_paso.html`, `obras/siguiente_paso_inicial.html`) en vez de quedarse en la misma lista — es un patrón deliberado (flujo guiado pedido explícitamente), no lo quites al tocar esas rutas.

## Arquitectura

- **App factory**: `constructora/__init__.py` (`create_app(config_class)`). Registra un blueprint por dominio: `auth`, `portal`, `main`, `clientes`, `levantamientos`, `cotizaciones`, `obras`, `usuarios`, `trabajadores`.
- **Auth interna**: `Flask-Login` con sesiones de cookie (`SESSION_COOKIE_HTTPONLY`/`SECURE`/`SAMESITE`), no JWT. `Usuario` (rol: admin/supervisor/empleado) y `ClienteAcceso` (portal) comparten el mismo `login_manager` mediante un `get_id()` compuesto (`"usuario:<id>"` / `"cliente:<id>"`), resuelto en el `user_loader` de `__init__.py`. `current_user.tipo` distingue cuál es cuál. `constructora/decorators.py` (`roles_requeridos(...)`, `solo_cliente_portal`) hace las veces del viejo middleware de roles.
- **Rate limiting de login**: `Flask-Limiter`, 8 intentos/15 min, aplicado en `auth.login` y `portal.login` (`constructora/auth.py`, `constructora/portal.py`).
- **Mano de obra separada de gastos**: `PagoManoObra` (ligado a `Trabajador`, con `oficio`) es un modelo aparte de `Gasto` — la categoría `mano_obra` ya NO existe en `Gasto.categoria`. Si agregas un nuevo tipo de costo, decide primero si es "alguien que cobra por su trabajo" (va a `PagoManoObra`/`Trabajador`) o "algo que se compra" (va a `Gasto`).
- **Cotizaciones versionadas**: `Cotizacion.version` + `Levantamiento.siguiente_version` — al rechazar una cotización, la UI ofrece crear una nueva versión del mismo levantamiento en vez de editar la rechazada. `Cotizacion.total` es una `@property` calculada desde `CotizacionItem` (nunca un campo guardado), pero `Obra.monto_contrato` sí es un snapshot congelado al momento de aceptar — coherente con cómo `estimaciones` ya congelaba precios en el sistema anterior.
- **Portal del cliente**: `constructora/portal.py`, aislado por `ClienteAcceso.cliente_id`; toda consulta de obra filtra `Obra.query.filter_by(id=obra_id, cliente_id=current_user.cliente_id)` — nunca actualices esas vistas para hacer `Obra.query.get(obra_id)` a secas, es exactamente el bug de aislamiento que las pruebas (`tests/test_flujo_completo.py::test_portal_cliente_no_ve_obras_de_otro_cliente`) existen para detectar.
- **Base de datos**: SQLAlchemy contra MySQL (`PyMySQL`). No hay migraciones tipo Alembic todavía — `flask --app wsgi init-db` corre `db.create_all()` (no destructivo, no altera columnas existentes). Para cambios de esquema en producción, por ahora hay que migrar a mano; si el esquema empieza a cambiar seguido, vale la pena meter Flask-Migrate.
- **Documentos**: igual que antes, solo se guarda la referencia (`url_archivo`) en `Documento`, con flag `visible_cliente` — no hay almacenamiento binario propio.

## Comandos

```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # define SECRET_KEY y DB_* — la app no arranca sin ellos
python -m flask --app wsgi init-db      # crea tablas (no destructivo)
python seed.py                           # ALTERNATIVA: borra todo y carga el escenario de ejemplo
python wsgi.py                           # http://localhost:5000
pytest tests/ -v                         # corre contra SQLite en memoria, no necesita MySQL
```

## Despliegue

Todo en Railway, un proyecto (`app-constructora`) con 2 servicios: el servicio Python (Gunicorn, `Procfile`: `web: gunicorn wsgi:app`) y `MySQL`. Conectado al repo de GitHub (`JGonza10/App_Constructora`, rama `master`) para redeploy automático. `DB_NAME` en Railway debe apuntar al nombre real de la base que usa la app (revisa qué nombre quedó configurado — el sistema anterior tuvo un bug por esto: `CREATE DATABASE constructora` en el SQL vs. `railway`, el nombre por defecto que da Railway).
