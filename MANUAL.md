# Manual del Sistema Constructora

_Manual de usuario del sistema de administración de obra para la constructora de Juan Gonzalez Mendoza ("Gonza"). Refleja el estado del código al 2026-09-08. Si algo de aquí ya no coincide con lo que ves en pantalla, el código manda sobre este documento — regenera los formatos imprimibles con `python generar_manual.py`._

## 1. Qué es y cómo entra cada quien

Aplicación web (Flask) para llevar toda la operación de una constructora: desde que un cliente pide una cotización hasta que la obra se termina y se cobra. Hay dos formas de entrar:

- **Equipo interno** (`/login`): admin, supervisor o empleado. Cada rol ve y puede hacer cosas distintas — un empleado registra gastos y avances, pero solo admin/supervisor aprueban cotizaciones, aceptan órdenes de cambio o ven reportes de rentabilidad.
- **Portal del cliente** (`/portal/login`): acceso de solo lectura (más aceptar/rechazar su propia cotización) para que el cliente vea el avance de su obra sin necesitar una cuenta interna.

## 2. El flujo que gobierna todo

```
Cliente -> Levantamiento (que pidio) -> Cotizacion (version por version)
   -> [al ACEPTARSE] nace la Obra, con el contrato = total de esa cotizacion
      -> gastos, mano de obra, avance, tareas, bitacora, documentos, pagos...
```

No existe un botón para crear una obra directo — nace sola al aceptar una cotización, para que el monto de contrato nunca se desincronice de lo cotizado. Cada pantalla de creación te lleva después a una de "¿qué sigue?" con los siguientes pasos típicos, en vez de dejarte adivinar.

## 3. Clientes, levantamientos y cotizaciones

- **Clientes**: alta con nombre, tipo (persona física/empresa), contacto, RFC. Buscador por nombre/email/teléfono/RFC en la lista.
- **Levantamiento**: lo que el cliente pidió (indicaciones, tipo de obra, dirección, fecha de visita).
- **Cotización**: se arma línea por línea (concepto, unidad, cantidad, precio unitario). Se puede:
  - Cargar conceptos del **catálogo de precios** (menú "Más → Catálogo de conceptos") con un clic, en vez de teclear cada uno.
  - Cargar una **plantilla completa** ("Más → Plantillas de cotización") — paquetes predefinidos por tipo de obra (ej. "Casa 100m²") que reemplazan todas las líneas de un jalón.
  - Descargarse en **PDF** para mandarla al cliente.
  - Tiene versiones (v1, v2...): si se rechaza, se crea una nueva versión del mismo levantamiento sin perder el historial. Cuando hay más de una versión, un botón "Comparar versiones" las pone lado a lado.
- **Aceptar/rechazar**: lo puede hacer el equipo interno (admin/supervisor) o el propio **cliente desde su portal**, con firma capturada a mano (dibujada con el dedo o el mouse) si quiere. En cuanto se acepta, nace la obra.

## 4. La obra — todo lo que pasa en campo

Cada obra tiene su pantalla de detalle con estas secciones (usa los botones "+ Nuevo" de cada una):

| Sección | Para qué |
|---|---|
| Gastos | Materiales, equipo, subcontratista, administrativo — con proveedor opcional. Exportable a CSV. |
| Mano de obra | Pagos a trabajadores por día/destajo/semana, separados de "gastos". |
| Avance semanal | % acumulado por etapa — alimenta la barra de progreso y la Curva S. |
| Tareas | Pendiente/en curso/terminada, con responsable y fecha límite. |
| Bitácora diaria | Clima, personal en obra, actividades, incidencias — con **fotos** adjuntas. |
| Documentos | Planos, licencias, contratos, actas, facturas — archivo real subido (no solo un link), visible o no al cliente, con fecha de vencimiento opcional (licencias/pólizas). |
| Pagos del cliente | Calendario de cobranza; los que se pasan de fecha se marcan "vencido" solos cada madrugada. |
| Inventario | Entradas y salidas de material — el sistema calcula la existencia sola del historial, no hay que llevarla aparte. |
| Órdenes de compra | Pedido a proveedor antes de pagar (solicitada → confirmada → recibida). Al marcarla "recibida" se genera el gasto real y entra al inventario en un solo paso. |
| Órdenes de cambio | Cuando el cliente pide algo fuera del alcance original: sube (o baja) el contrato de forma trazable, con aprobación — nunca se edita el monto a mano. |
| Seguridad e higiene | Checklist de EPP e incidentes — uno grave manda alerta al momento. |
| Asistencia | Checklist diario de quién de los trabajadores llegó a esa obra (independiente de a quién se le pagó). |
| Equipo asignado | Qué maquinaria (propia o rentada) está en esta obra y desde cuándo. |
| Subcontratistas | Contrato y % de avance propio, distinto de un simple "gasto". |
| Mensajes | Chat simple con el cliente, visible de los dos lados. |

Arriba de la obra también hay una gráfica de **flujo de caja mensual** (ingresos recibidos vs. gastos) y, para admin/supervisor, un link al **reporte de rentabilidad**.

## 5. Reportes y dinero

- **Reporte de rentabilidad** (por obra): contratado vs. gastado vs. margen vs. cobranza, más la **Curva S** (% de avance físico contra % del contrato ya gastado — si la línea roja va por delante de la azul, la obra está gastando más rápido de lo que avanza).
- **Dashboard** (inicio): obras activas, levantamientos sin cotizar, cotizaciones esperando respuesta, y una gráfica de **flujo de caja consolidado** de todas las obras activas juntas.
- **Nómina semanal** ("Más → Nómina"): agrupa los pagos de mano de obra por trabajador en la semana que elijas, con los días de asistencia al lado. Exportable a CSV.
- **Auditoría** (solo admin, "Más → Auditoría"): quién aceptó/rechazó qué cotización y quién aprobó qué orden de cambio — no un log general, solo lo que mueve dinero o el estado de una obra.

## 6. Alertas automáticas

El sistema avisa solo (por email y/o Telegram, si están configurados — si no, solo queda en el registro del servidor) cuando:
- Una obra cruza el 90% o el 100% de su presupuesto gastado.
- Un pago de cliente se vence sin cobrarse.
- Un documento con fecha de vencimiento (licencia, póliza) está a 30 días de caducar.
- Se registra un incidente de seguridad grave.

También avisa **al cliente por su correo** cuando hay un avance nuevo o un documento nuevo visible en su portal.

## 7. Trabajadores

Además del alta básica (nombre, oficio, teléfono, tipo de pago), cada trabajador tiene su propia ficha con:
- **Expediente**: identificación, contrato, examen médico, seguro — archivo real, con vencimiento opcional.
- **Vacaciones/incapacidades**: se marcan como ausencia y aparecen reflejadas en la nómina de esa semana.

## 8. Catálogos de apoyo

- **Catálogo de conceptos** ("Más"): banco de precios reutilizable al cotizar, exportable a CSV.
- **Plantillas de cotización** ("Más"): paquetes de conceptos por tipo de obra.
- **Equipo y maquinaria** ("Más"): inventario de equipo propio/rentado, con su costo de renta diario.
- **Subcontratistas** ("Más"): catálogo de subcontratistas con su especialidad, para asignarles contratos en las obras.

## 9. En el celular

La app es instalable como aplicación (PWA): desde el navegador del celular, "Agregar a pantalla de inicio" pone el ícono como cualquier app. Está pensada para que bitácora, gastos y asistencia se capturen desde el celular en obra, no solo desde escritorio.

## 10. Instalación y arranque (para quien administre el servidor)

```powershell
venv\Scripts\activate
copy .env.example .env              # define SECRET_KEY, DB_* y (opcional) ALERTAS_*
flask --app wsgi db upgrade         # aplica el esquema completo
flask --app wsgi crear-admin --email tu@correo.com --password "Algo#Seguro1" --nombre "Tu Nombre"
python wsgi.py                      # http://localhost:5000
```

Desarrollo local: como el MySQL nativo de esta máquina perdió su contraseña de root, el ambiente de desarrollo usa un MySQL propio en Docker (`docker compose -f docker-compose.local.yml up -d`, puerto 3307) — no toca el MySQL del sistema. Producción sigue en Railway, desplegado automáticamente al hacer push al repositorio de GitHub.

## 11. Lo que todavía no hace

- No timbra facturas (CFDI) — los documentos "factura" son solo el archivo, no facturación electrónica real.
- No calcula nómina fiscal (ISR/IMSS) — la "nómina semanal" es un resumen de pagos, no un sistema de recursos humanos completo.
- Las alertas por email/Telegram necesitan configurarse (`.env`) — sin eso, solo quedan en el registro del servidor, nadie las recibe.
