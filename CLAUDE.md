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
- **Documentos**: `Documento.url_archivo` guarda **o** una URL externa **o** una referencia `local:<ruta>` a un archivo real subido a `instance/uploads/` (mismo patrón que `local:<archivo>` en Chicos Wheels/CollectHub) — `constructora/archivos.py` decide cuál es cuál. Se sirve por `/obras/<id>/documentos/<id>/descargar`, que valida que un cliente del portal solo vea el suyo y solo si `visible_cliente=True`. Las fotos de bitácora (`BitacoraFoto`) siguen el mismo mecanismo de guardado.

## Funcionalidades agregadas 2026-09-08

Doce funcionalidades nuevas sobre la base anterior, todas con prueba en `tests/test_funcionalidades_nuevas.py`:

- **PDF de cotización** (`constructora/pdf.py`, reportlab — sin dependencias nativas): `GET /cotizaciones/<id>/pdf`.
- **Aceptar/rechazar cotización desde el portal del cliente**: `crear_obra_desde_cotizacion()` y `rechazar_cotizacion()` en `cotizaciones.py` son el único camino compartido — tanto la ruta interna (`cotizaciones.aceptar`) como la del portal (`portal.aceptar_cotizacion`) los llaman, para no duplicar el invariante de "una obra nace en un solo lugar".
- **Alertas de sobrepresupuesto** (`constructora/alertas.py`): se dispara al registrar un `Gasto` o `PagoManoObra`. `Obra.nivel_alerta_presupuesto` (0/90/100) evita reavisar por cada gasto nuevo una vez cruzado un umbral.
- **Vencimiento automático de pagos de cliente** (`constructora/tareas_programadas.py`): job diario de APScheduler (6:00 am, arrancado en `create_app`, con guardas para no duplicarse bajo el recargador de `flask run --debug` ni bajo tests) — también corre a mano con `flask --app wsgi vencer-pagos`.
- **Notificaciones** (`constructora/notificaciones.py`): email SMTP y/o Telegram, configurables por variables `ALERTAS_*` (ver `.env.example`); sin configurar, solo registra en el logger — nunca rompe el flujo que la disparó.
- **Catálogo de conceptos** (`ConceptoCatalogo` + blueprint `catalogo`, `/catalogo`): banco de precios reutilizable; el formulario de cotización (`cotizaciones/form.html`) lo carga como JSON y rellena la última línea al elegir uno.
- **Comparativo de versiones de cotización**: `GET /cotizaciones/levantamiento/<id>/comparar`.
- **Reporte de rentabilidad por obra**: `GET /obras/<id>/reporte-cierre` (monto contratado vs. gasto real vs. margen vs. cobranza).
- **Subida real de archivos** para documentos y fotos de bitácora (ver arriba, `archivos.py`). `MAX_CONTENT_LENGTH` en `config.py` limita a 15 MB por archivo.
- **Nómina semanal**: `GET /trabajadores/nomina?semana=YYYY-MM-DD` agrupa `PagoManoObra` por trabajador en la semana lunes-domingo que contiene esa fecha, sin importar la obra.
- **Gráfica de flujo de caja por obra**: Chart.js (CDN, mismo criterio que Bootstrap) en `obras/detalle.html`, con datos agregados por mes en `obras._flujo_caja()`.
- **Flask-Migrate**: wired en `extensions.py`/`__init__.py`. Sigue habiendo tablas nuevas creadas por `db.create_all()` (no requieren migración), pero `Obra.nivel_alerta_presupuesto` es una columna nueva sobre una tabla existente — **necesita** `flask --app wsgi db upgrade` (o un `ALTER TABLE` a mano) contra cualquier base que ya tenga datos, antes de que ese código corra ahí. Corre `flask --app wsgi db init && flask --app wsgi db migrate -m "baseline" && flask --app wsgi db upgrade` una sola vez para adoptarlo en una base existente.

**Usuarios**: además de `usuarios/nuevo` (requiere sesión de admin), `flask --app wsgi crear-admin --email ... --password ... --nombre "..." --rol admin` crea o actualiza (contraseña/rol) un usuario sin necesitar sesión previa — pensado para el primer arranque o para restablecer una contraseña sin usar `seed.py` (que borra todos los datos).

**Desarrollo local**: el MySQL nativo de esta máquina (AppServ, puerto 3306) tiene la contraseña de root perdida — en vez de tocarlo, el dev local usa un MySQL propio en Docker (`docker-compose.local.yml`, puerto 3307, credenciales en `.env` gitignored). `docker compose -f docker-compose.local.yml up -d` lo levanta; ya tiene el esquema completo aplicado vía Alembic (`flask --app wsgi db upgrade`) y un usuario admin (`juangonza@live.com.mx`).

## Funcionalidades agregadas 2026-09-08 (segunda tanda)

Veinte funcionalidades más, todas con prueba en `tests/test_funcionalidades_v2.py` y verificadas también en vivo contra MySQL real (no solo SQLite de pytest):

- **Inventario de materiales por obra** (`MovimientoInventario`, sin tabla de saldo — `Obra.inventario_resumen()` lo recalcula del historial de entradas/salidas, igual criterio que `gasto_real`): `/obras/<id>/inventario/nuevo`.
- **Órdenes de compra** (`OrdenCompra`, estados solicitada→confirmada→recibida/cancelada): `obras.recibir_orden_compra` genera el `Gasto` real y la entrada de inventario en una sola acción, no dos pasos manuales.
- **Asistencia diaria** (`Asistencia`, independiente de `PagoManoObra` — una es "quién llegó", la otra "a quién se le pagó"): checklist en `/obras/<id>/asistencia`, alimenta la columna "días asistidos" de la nómina.
- **Expediente digital del trabajador** (`DocumentoTrabajador`, mismo mecanismo de `archivos.py`) y **vacaciones/incapacidades** (`AusenciaTrabajador`) — ambos colgados de `trabajadores.detalle`, visibles también en la nómina semanal.
- **Equipo y maquinaria** (`Equipo` + `AsignacionEquipo`): blueprint `equipo`, asignación/liberación por obra.
- **Órdenes de cambio** (`OrdenCambio`): único camino para mover `Obra.monto_contrato` después de que la obra ya nació — `obras.resolver_orden_cambio` lo hace trazable (queda la orden) y auditado, nunca se edita el campo a mano.
- **Seguridad e higiene** (`IncidenteSeguridad`, distinto de la bitácora general): incidente grave dispara `notificar()`.
- **Curva S** (`obras._curva_s()`): % avance físico vs. % del contrato ya gastado, graficado en el reporte de rentabilidad.
- **Dashboard consolidado**: `main._flujo_caja_consolidado()` suma el flujo de caja de todas las obras activas (la versión "toda la empresa" de `obras._flujo_caja()`).
- **Exportar a CSV**: gastos por obra (`obras.exportar_gastos_csv`), catálogo (`catalogo.exportar_csv`), nómina semanal (`trabajadores.nomina_exportar_csv`) — `csv`/`io` de la stdlib, sin dependencia nueva.
- **Auditoría de acciones críticas** (`constructora/auditoria.py`, `RegistroAuditoria`): `auditoria.registrar(...)` se llama al aceptar/rechazar una cotización y al aprobar una orden de cambio — no es un log general, solo lo que mueve dinero o estado de obra. Vista en `/auditoria` (solo admin).
- **Notificación automática al cliente** (`notificaciones.notificar_cliente()`): al registrar un avance o un documento visible, si el cliente tiene email.
- **Vencimientos de documentos legales**: `Documento.fecha_vencimiento` + `tareas_programadas.avisar_documentos_por_vencer()` (30 días antes, un solo aviso por documento vía `aviso_vencimiento_enviado`), corre en el mismo job diario que vence pagos.
- **Subcontratistas como entidad propia** (`Subcontratista` + `ContratoSubcontratista`, con su propio avance %) — distinto de `Proveedor`/`Gasto` categoría "subcontratista".
- **Plantillas de cotización** (`PlantillaCotizacion` + `PlantillaItem`, blueprint `plantillas`): se cargan de un clic en `cotizaciones/form.html` (`accion=cargar_plantilla`), reemplazando las líneas actuales.
- **Búsqueda y filtros avanzados**: `obras.lista` acepta `q` (nombre de obra o cliente), `responsable_id`, `desde`/`hasta` (fecha de inicio); `clientes.lista` acepta `q` (nombre/email/teléfono/RFC).
- **Firma digital** (`Cotizacion.firma_url`): canvas HTML5 en `portal/cotizacion_detalle.html`, capturado como PNG base64 y guardado por `cotizaciones.guardar_firma_cotizacion()` solo si el cliente realmente trazó algo (canvas vacío no cuenta como firma).
- **Mensajería obra↔cliente** (`MensajeObra`): hilo simple en `obras/detalle.html` y `portal/obra_detalle.html`, sin editar/borrar.
- **PWA instalable** (`static/manifest.json`, `static/sw.js`, íconos generados con Pillow): el service worker **no cachea nada a propósito** — casi toda la app son formularios con CSRF y sesión, y servir una página vieja del cache rompe el siguiente POST con un token caducado. El valor es "instalar en la pantalla de inicio", no trabajar offline.
- **CSRF en formularios sin WTForms**: de paso se encontraron y corrigieron varios botones-formulario preexistentes (`marcar_pago_recibido`, `toggle_visibilidad_documento`, `cambiar_estado_tarea`, `cotizaciones.enviar`, `usuarios.toggle_estado`, `catalogo.eliminar`, aceptar cotización del portal) que no mandaban `csrf_token` — con `WTF_CSRF_ENABLED=True` (producción) habrían fallado con 400 al primer clic; en pytest no se detectaba porque `TestConfig` desactiva CSRF. Cualquier form nuevo que no use `form.hidden_tag()` necesita `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` a mano.

## Comandos

```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # define SECRET_KEY y DB_* — la app no arranca sin ellos
python -m flask --app wsgi init-db      # crea tablas nuevas (no destructivo, no altera columnas existentes)
python -m flask --app wsgi db upgrade   # aplica migraciones pendientes (columnas nuevas en tablas existentes)
python -m flask --app wsgi crear-admin --email tu@correo.com --password "Algo#Seguro1" --nombre "Tu Nombre"
python -m flask --app wsgi vencer-pagos # corre a mano el job diario de pagos de cliente vencidos
python seed.py                           # ALTERNATIVA: borra todo y carga el escenario de ejemplo
python wsgi.py                           # http://localhost:5000
pytest tests/ -v                         # corre contra SQLite en memoria, no necesita MySQL
```

## Despliegue

Todo en Railway, un proyecto (`app-constructora`) con 2 servicios: el servicio Python (Gunicorn, `Procfile`: `web: gunicorn wsgi:app`) y `MySQL`. Conectado al repo de GitHub (`JGonza10/App_Constructora`, rama `master`) para redeploy automático. `DB_NAME` en Railway debe apuntar al nombre real de la base que usa la app (revisa qué nombre quedó configurado — el sistema anterior tuvo un bug por esto: `CREATE DATABASE constructora` en el SQL vs. `railway`, el nombre por defecto que da Railway).
