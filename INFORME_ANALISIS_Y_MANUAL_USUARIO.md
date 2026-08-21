# Informe de análisis y Manual de Usuario — Sistema Constructora (v2)

**Fecha:** 2026-08-21
**Qué cambió respecto a la v1 de este informe:** el sistema completo (backend Node.js/Express + frontend React) se reescribió desde cero en Python/Flask, con un modelo de datos nuevo. Este documento reemplaza la versión anterior por completo.

---

## Índice

1. [Por qué se reescribió el sistema](#1-por-qué-se-reescribió-el-sistema)
2. [Cómo está armado ahora](#2-cómo-está-armado-ahora)
3. [Roles y qué puede hacer cada uno](#3-roles-y-qué-puede-hacer-cada-uno)
4. [Revisión de seguridad](#4-revisión-de-seguridad)
5. [Plan para la app móvil](#5-plan-para-la-app-móvil)
6. [Manual de Usuario — el flujo guiado, paso a paso](#6-manual-de-usuario--el-flujo-guiado-paso-a-paso)
7. [Qué quedó fuera de esta versión (fase 2)](#7-qué-quedó-fuera-de-esta-versión-fase-2)
8. [Checklist antes de producción](#8-checklist-antes-de-producción)

---

## 1. Por qué se reescribió el sistema

El sistema anterior (Node/Express + React) tenía un problema de fondo, no de interfaz: **el formulario para crear una obra pedía el monto final del contrato antes de que existiera ninguna cotización.** Además:

- `Cliente` no tenía forma de capturar qué había pedido — era solo un directorio de contacto.
- `Presupuesto` y `Obra.monto_contrato` eran dos números capturados por separado que nunca se sincronizaban: podías aprobar un presupuesto de $620,000 y la obra seguía diciendo $1,950,000.
- El estado `cotizacion` vivía *dentro* de `Obra.estado`, cuando una cotización debería existir *antes* de que la obra exista.

Se comparó contra el patrón que usan JobTread, Buildertrend y (más cercano a México) Presupix/MAEC: **Cliente → Levantamiento → Cotización → al aceptarse, se convierte en la Obra.** Es el mismo patrón que se implementó aquí. Fuentes de esa investigación: [JobTread](https://www.jobtread.com/news/jobtread-opens-a-migration-path-for-builders-facing-the-coconstruct-phase-out), [Presupix](https://presupix.com/mx/blog/software-gestion-obras-independientes), [MAEC](https://maec.ai/software-presupuesto-construccion-mexico/).

Encima, se pidió que el flujo fuera **guiado**: cada formulario, al guardarse, debe ofrecer el siguiente paso lógico (en vez de una pantalla con pestañas sueltas donde hay que adivinar a dónde ir), y que la mano de obra por oficio (albañiles, pintores, etc.) se registre aparte de los gastos de materiales, no mezclada en una sola categoría de texto libre.

---

## 2. Cómo está armado ahora

**Stack**: Python 3 + Flask, monolítico (sin API/frontend separados) — Jinja2 + Bootstrap 5, MySQL vía SQLAlchemy, sesiones de `Flask-Login` en vez de JWT.

**El flujo**, de principio a fin:

```
Cliente
  └─ Levantamiento (qué pidió, dirección, fecha de visita)
       └─ Cotización v1, v2... (línea por línea: concepto, unidad, cantidad, precio)
            ├─ borrador → enviada → aceptada  → nace la Obra (monto_contrato = total de la cotización)
            └─                    → rechazada → se puede crear una nueva versión
                                                     │
                    Obra ───────────────────────────┘
                     ├─ Gastos (materiales, equipo, subcontratista, administrativo, otro)
                     ├─ Pagos de mano de obra (por Trabajador: albañil, pintor, electricista...)
                     ├─ Avance semanal
                     ├─ Tareas
                     ├─ Bitácora diaria
                     ├─ Documentos (con flag visible_cliente)
                     └─ Pagos programados del cliente
```

Todo lo que cuelga de una obra usa `obra_id` como llave — dos obras nunca comparten gastos, pagos, avances, etc. Esto ya se probó automáticamente (ver sección 4).

---

## 3. Roles y qué puede hacer cada uno

| Módulo | Admin | Supervisor | Empleado | Cliente (portal) |
|---|---|---|---|---|
| Usuarios internos | crear/activar | ver | — | — |
| Clientes | ✅ | crear/editar | ver | — |
| Levantamientos | ✅ | ✅ | ✅ (captura) | — |
| Cotizaciones (crear/enviar) | ✅ | ✅ | ✅ | — |
| Cotizaciones (aceptar/rechazar → crea la obra) | ✅ | ✅ | ❌ | — |
| Gastos / mano de obra / avance / tareas / bitácora | ✅ | ✅ | ✅ | ver solo lo de su obra (avance) |
| Documentos (visibilidad al cliente) | ✅ | ✅ | subir | ver solo los marcados visibles |
| Pagos del cliente (programar/marcar recibido) | ✅ | ✅ | ver | ver estado de cuenta de su obra |
| Trabajadores (alta) | ✅ | ✅ | ✅ | — |

El cliente del portal (`ClienteAcceso`) es un sistema de login totalmente aparte de `Usuario` — comparte el mismo mecanismo de sesión de Flask-Login, pero nunca puede terminar autenticado como un usuario interno ni viceversa (`current_user.tipo` se valida en cada vista protegida).

---

## 4. Revisión de seguridad

| Punto | Estado |
|---|---|
| Contraseñas hasheadas (nunca texto plano) | ✅ `Flask-Bcrypt`, igual que antes pero ahora también para el `SECRET_KEY`/sesión, no solo la contraseña |
| Token de sesión accesible por JavaScript (el problema pendiente de la v1) | ✅ **Resuelto** — ya no hay JWT en `localStorage`; la sesión vive en una cookie `HttpOnly` + `Secure` + `SameSite=Lax`, invisible para JS incluso ante un XSS |
| CSRF | ✅ `Flask-WTF` protege todos los formularios (antes no aplicaba porque no había cookies) |
| Fuerza bruta en login | ✅ `Flask-Limiter`, 8 intentos/15 min, en login interno y portal |
| SQL Injection | ✅ Todo pasa por el ORM (SQLAlchemy) con parámetros — no hay SQL armado a mano |
| Secretos fuera del código | ✅ `SECRET_KEY`/`DB_PASSWORD` desde variables de entorno, la app no arranca sin ellos |
| Validación de complejidad de contraseña | ✅ mínimo 8 caracteres al crear usuarios internos (`UsuarioForm`) — pendiente hacerlo también configurable/más estricto si se abre registro público |
| HTTPS | ✅ Railway lo sirve automáticamente en el dominio `*.up.railway.app` |

**Lo que sigue pendiente** (igual que en la v1, no cambió con la reescritura):
- Bloqueo explícito de cuenta tras intentos fallidos (hoy solo hay límite por IP, no un flag en la cuenta).
- Aviso de privacidad (LFPDPPP) — el sistema guarda datos personales de clientes (nombre, email, teléfono, RFC) además de los tuyos.

---

## 5. Plan para la app móvil

No cambia respecto a lo ya planteado: al ser Flask con sesiones de cookie servidas por HTTPS, una futura app móvil nativa tendría que decidir entre (a) usar una vista web embebida (WebView) apuntando directo a este mismo sitio — la opción más simple, cero código nuevo de backend — o (b) exponer endpoints JSON aparte para una app 100% nativa, lo cual sí implicaría volver a un esquema de token (ya no cookies, que no viajan bien fuera del navegador) y aplicar ahí las mismas reglas: almacenamiento seguro en el dispositivo (`expo-secure-store`/`react-native-keychain`), nunca en almacenamiento plano. Dado que hoy es un monolito Flask server-rendered, la opción (a) — WebView — es la más barata y consistente con "empezamos de cero, simple".

---

## 6. Manual de Usuario — el flujo guiado, paso a paso

Credenciales de ejemplo (cargadas por `python seed.py`):

| Rol | Email | Contraseña |
|---|---|---|
| admin | `ana.ramirez@constructora.com` | `Direccion#2026` |
| supervisor | `jorge.villasenor@constructora.com` | `Supervisa#2026` |
| empleado | `paola.reyes@constructora.com` | `Campo#2026` |
| portal (Familia Delgado Ríos) | `delgado.rios@example.com` | `Cliente#2026` |
| portal (Grupo Constructor Altavista) | `contacto@altavista.mx` | `Altavista#2026` |

### Paso 1 — Cliente nuevo (rol supervisor o admin)

Entra, ve a **Clientes → + Nuevo cliente**, llena nombre/tipo/contacto y guarda. El sistema **te lleva directo** a la pantalla de "Nuevo levantamiento" con ese cliente ya preseleccionado — no hace falta ir a buscarlo.

### Paso 2 — Levantamiento (qué pidió el cliente)

Captura el título, tipo de obra, dirección y, lo más importante, **"¿Qué pidió el cliente?"** — el campo de indicaciones es obligatorio a propósito: es el origen de todo lo demás. Al guardar, aparece una pantalla puente ofreciendo **"Crear cotización ahora"**.

### Paso 3 — Cotización, línea por línea

Cada línea es un concepto con unidad, cantidad y precio unitario — el total se calcula solo, nunca se teclea a mano. Botón **"+ Agregar línea"** para más conceptos. Al guardar queda en **borrador**; desde el detalle de la cotización:
- **"Marcar como enviada al cliente"** → pasa a estado *enviada*.
- Ya enviada, aparecen dos cajas: **"El cliente aceptó"** (crea la obra) o **"El cliente rechazó"** (pide motivo, y desde el levantamiento puedes armar una v2).

### Paso 4 — La obra nace sola

Al aceptar, aparece: *"🎉 Obra '...' en marcha — Contrato por $X"*, con dos botones grandes: **registrar el primer gasto de materiales** o **el primer pago de mano de obra**. El monto de contrato es exactamente el total de la cotización — no se vuelve a teclear.

### Paso 5 — Operación diaria (rol empleado, admin o supervisor)

Desde el detalle de la obra: gastos, pagos de mano de obra (elige el trabajador por oficio — si no existe, el propio formulario te manda a darlo de alta y te trae de vuelta), avance semanal, tareas, bitácora, documentos. Cada guardado te ofrece el siguiente registro típico (ej. después de un avance, sugiere la bitácora del día).

### Paso 6 — Portal del cliente

Entra en `/portal/login` (login aparte). Solo ve su(s) obra(s), avance, estado de cuenta y documentos marcados como visibles. Prueba de aislamiento: entra con el otro cliente de ejemplo y confirma que **no** ve la obra del primero.

---

## 7. Qué quedó fuera de esta versión (fase 2)

Para no entregar un sistema grande a medias, se dejó fuera deliberadamente lo que no es parte del flujo central pedido:

- Catálogo de materiales / calculadora de estimaciones (existía en la v1 anterior).
- Órdenes de compra a proveedores (proveedores en sí sí quedó, mínimo, para poder ligarlo a un gasto).
- Exportación a Excel/PDF.
- Tablero ejecutivo con gráficas (hay un dashboard con números, sin Chart.js).
- Alertas en tiempo real (Socket.io ya no aplica en un monolito Flask server-rendered).

Nada de esto se perdió por accidente — si alguno hace falta, es un blueprint más siguiendo el mismo patrón que los demás.

---

## 8. Checklist antes de producción

- [ ] Definir `SECRET_KEY` y credenciales de MySQL de producción (no reusar las de desarrollo).
- [ ] Cambiar o eliminar las 5 cuentas de ejemplo antes de exponer el sistema a internet.
- [ ] Redactar el aviso de privacidad (LFPDPPP) para los datos de clientes.
- [ ] Decidir un flujo de "cambiar contraseña" para el portal del cliente (hoy no existe; la contraseña inicial es la que se le entrega).
- [ ] Configurar backups automáticos de MySQL en Railway.
- [ ] Meter Flask-Migrate si el esquema empieza a cambiar seguido (hoy `init-db` solo crea tablas nuevas, no altera columnas existentes).
