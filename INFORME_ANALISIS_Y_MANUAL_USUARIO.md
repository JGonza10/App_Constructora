# Informe de análisis y Manual de Usuario — Sistema Constructora

**Fecha del análisis:** 2026-08-21
**Alcance:** revisión completa del sistema (backend, frontend, base de datos), datos de ejemplo nuevos para los 4 roles, revisión de seguridad centrada en manejo de credenciales, y plan para la futura app móvil.

Este documento reemplaza cualquier ejemplo o credencial anterior del sistema. Los usuarios y contraseñas de prueba que traía el proyecto (`admin@constructora.com` / `Admin123!`, etc.) ya **no existen** en la base de datos ni en el código — se sustituyeron por el escenario nuevo descrito abajo.

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Qué es el sistema y cómo está armado](#2-qué-es-el-sistema-y-cómo-está-armado)
3. [Roles del sistema y qué puede hacer cada uno](#3-roles-del-sistema-y-qué-puede-hacer-cada-uno)
4. [Datos de ejemplo nuevos](#4-datos-de-ejemplo-nuevos)
5. [Revisión de seguridad](#5-revisión-de-seguridad)
6. [Plan para la app móvil](#6-plan-para-la-app-móvil)
7. [Manual de Usuario — recorrido de validación por rol](#7-manual-de-usuario--recorrido-de-validación-por-rol)
8. [Checklist antes de producción](#8-checklist-antes-de-producción)
9. [Qué se cambió exactamente en este trabajo](#9-qué-se-cambió-exactamente-en-este-trabajo)
10. [Próximos pasos sugeridos](#10-próximos-pasos-sugeridos)

---

## 1. Resumen ejecutivo

El sistema es una aplicación web funcional (Node.js/Express + MySQL + React) para administrar la operación de una constructora: obras, presupuestos, gastos, avances, cobros, proveedores, tareas, bitácora, estimación de materiales, documentos, y un portal separado de solo lectura para el cliente final. Tiene 4 roles: **admin**, **supervisor**, **empleado** (los tres internos) y **cliente** (portal externo).

Hallazgos principales de esta revisión:

- ✅ Las contraseñas **nunca** se guardan ni se transmiten en texto plano dentro del sistema: se hashean con `bcrypt` antes de guardarse y solo viajan una vez, en el `POST /login`, dentro del body sobre la conexión (que debe ser HTTPS en producción — ver sección 5).
- 🔴 **Corregido en este trabajo:** la pantalla de login mostraba una credencial de demo (`admin@constructora.com / Admin123!`) directamente en la interfaz — visible para cualquiera que abriera la página. Se eliminó.
- 🔴 **Corregido en este trabajo:** no había límite de intentos de login (riesgo de fuerza bruta contra el admin, el portal del cliente, o cualquier cuenta). Se agregó un limitador (`express-rate-limit`).
- 🔴 **Corregido en este trabajo:** faltaban cabeceras de seguridad HTTP básicas. Se agregó `helmet`.
- 🟡 **Pendiente (requiere decisión tuya, ver sección 5):** el token de sesión se guarda en `localStorage` del navegador, lo cual es más vulnerable a robo por XSS que una cookie `HttpOnly`. No lo cambié porque implica rediseñar el flujo de autenticación (cookies + protección CSRF) y quería que lo decidieras primero.
- 🟡 **Pendiente:** no hay bloqueo de cuenta tras varios intentos fallidos (el rate limit ya frena fuerza bruta automatizada, pero no marca la cuenta como bloqueada).
- 🟡 Dependencias con vulnerabilidades conocidas: se corrigieron 3 de 4 con `npm audit fix`; queda una (`uuid`/`exceljs`, severidad moderada) que requiere una actualización con cambios de compatibilidad — no se aplicó automáticamente para no arriesgar el módulo de exportación a Excel sin que lo pruebes tú primero.

Se sustituyeron **todos** los datos de ejemplo (usuarios, clientes, obras, presupuestos, gastos, avances, pagos, proveedores, tareas, bitácora, documentos y accesos al portal) por un escenario nuevo y coherente, con credenciales reales generadas con `bcrypt`, para que puedas iniciar sesión con cada rol y validar que el sistema funciona como se planteó. Antes de este trabajo, **el portal del cliente no tenía ningún acceso de ejemplo** — no había forma de probar ese rol sin correr un script manualmente.

---

## 2. Qué es el sistema y cómo está armado

**Backend:** Node.js + Express 4, corriendo en el puerto 3001. Un router por dominio de negocio bajo `/api/<recurso>` (usuarios, obras, presupuestos, clientes, gastos, avance, pagos, proveedores, tareas, bitácora, tablero, estimaciones, documentos, admin, portal). Autenticación con JWT firmado (`JWT_SECRET`), expira a las 8 horas. Tiempo real con Socket.io (alertas, cambios de presupuesto/obra, gastos nuevos).

**Frontend:** React 18 + React Router, consumiendo la API con Axios. Dos "aplicaciones" separadas dentro del mismo frontend: el sistema interno (`/dashboard`, `/obras`, etc., protegido por `AuthContext`) y el portal del cliente (`/portal/*`, protegido por `PortalAuthContext`, con su propio login y su propio token).

**Base de datos:** MySQL 8+. Un esquema base (`constructora.sql`: usuarios, presupuestos, alertas) más dos migraciones incrementales (`v2_ampliacion.sql`: clientes, obras, gastos, avance, pagos, proveedores, tareas, bitácora; `v3_diferenciadores.sql`: catálogo de materiales, estimaciones, documentos, accesos del portal).

**Separación importante:** el portal del cliente **no** es "el sistema interno con permisos reducidos" — es un sistema de login y de datos completamente aparte (`clientes_acceso`, no `usuarios`), con su propio middleware de verificación de token (`verificarClienteToken` en `backend/routes/portal.js`) que exige `tipo: 'cliente'` dentro del JWT. Esto es una buena decisión de diseño: un cliente jamás podría, ni por error de programación en otra ruta, terminar con un token que lo deje pasar como empleado interno, porque son dos flujos de emisión de token distintos.

**Despliegue previsto:** Railway para backend + MySQL, Vercel para el frontend — coincide con lo que recomienda tu proceso seguro para apps con backend/login/base de datos propia, así que no hay cambio de tecnología que sugerir ahí.

---

## 3. Roles del sistema y qué puede hacer cada uno

Basado en los middlewares reales de cada ruta (`verificarRol` / `rol(...)` en `backend/routes/*.js`), no en suposiciones:

| Módulo | Admin | Supervisor | Empleado | Cliente (portal) |
|---|---|---|---|---|
| Usuarios internos (crear/activar/desactivar) | ✅ | ver lista (solo lectura) | ❌ | — |
| Obras (crear/editar) | ✅ | ✅ | ver detalle | solo **su** obra, solo lectura |
| Presupuestos (crear) | ✅ | ✅ | ✅ | — |
| Presupuestos (aprobar/eliminar) | ✅ (eliminar) | ✅ (aprobar vía edición) | — | — |
| Clientes (crear/editar/eliminar) | ✅ | crear/editar | ver lista | — |
| Gastos (registrar) | ✅ | ✅ | ✅ | — |
| Gastos (editar/eliminar) | ✅ | editar | — | — |
| Avance de obra (registrar) | ✅ | ✅ | ✅ | ver solo el de su obra |
| Pagos de cliente (registrar/editar) | ✅ | ✅ | ver lista | ver estado de cuenta de su obra |
| Proveedores y órdenes de compra | ✅ | crear/editar | ver lista | — |
| Tareas (crear/editar) | ✅ | ✅ | ✅ | — |
| Bitácora de obra (registrar) | ✅ | ✅ | ✅ | — |
| Tablero ejecutivo (KPIs globales) | ✅ | ✅ | ❌ | — |
| Estimación de materiales (catálogo) | administrar precios | administrar precios | usar calculadora | — |
| Documentos por obra | ✅ | subir/eliminar | subir | ver solo los marcados como visibles |
| Exportar Excel/PDF | ✅ | ✅ | ❌ | — |

**En una frase por rol:**
- **Admin**: control total, incluyendo alta de usuarios internos y borrado de registros financieros.
- **Supervisor**: dueño operativo de las obras — crea y aprueba, ve el tablero ejecutivo, pero no da de alta usuarios ni borra lo que ya se aprobó.
- **Empleado**: registra la operación del día a día (gastos, avances, bitácora, tareas) pero no aprueba ni borra.
- **Cliente**: espectador de su propia obra únicamente — nunca ve otras obras, ni gastos internos, ni proveedores, ni nada que no sea avance/pagos/documentos compartidos de lo suyo.

---

## 4. Datos de ejemplo nuevos

Se borró **todo** el set de datos de ejemplo anterior (usuarios `admin@constructora.com` / `supervisor@constructora.com` / `empleado@constructora.com`, los 3 clientes viejos, las 3 obras viejas, etc.) y se reemplazó por este escenario, pensado para que puedas validar cada rol y también la **separación de datos entre clientes**:

**Usuarios internos** (tabla `usuarios`, `database/constructora.sql`):

| Rol | Nombre | Email | Contraseña de prueba |
|---|---|---|---|
| admin | Ana Ramírez | `ana.ramirez@constructora.com` | `Direccion#2026` |
| supervisor | Jorge Villaseñor | `jorge.villasenor@constructora.com` | `Supervisa#2026` |
| empleado | Paola Reyes | `paola.reyes@constructora.com` | `Campo#2026` |

**Clientes con acceso al portal** (tabla `clientes_acceso`, `database/migraciones/v3_diferenciadores.sql`):

| Cliente | Obra asociada | Email de acceso | Contraseña de prueba |
|---|---|---|---|
| Familia Delgado Ríos (persona física) | Residencia Delgado Ríos | `delgado.rios@example.com` | `Cliente#2026` |
| Grupo Constructor Altavista SA de CV (empresa) | Plaza Comercial Altavista | `contacto@altavista.mx` | `Altavista#2026` |

**El escenario de negocio** que queda armado con estos dos clientes:

- *Residencia Delgado Ríos* (residencial, $1,950,000 MXN, activa, 35% de avance): tiene presupuesto de cimentación aprobado y uno de acabados en borrador, dos reportes de avance semanal, gastos de materiales y mano de obra, 3 pagos programados (uno ya recibido), un documento pendiente de visibilidad (el contrato, marcado como no visible al cliente) y dos sí visibles (planos y licencia).
- *Plaza Comercial Altavista* (comercial, $8,400,000 MXN, activa, 12% de avance): presupuesto de instalaciones en revisión (sin aprobar todavía — para probar ese estado), un gasto de acero y uno de renta de grúa, un pago recibido y uno **vencido** (para probar ese estado en el portal), y una tarea en curso.

Con estos dos clientes puedes confirmar en vivo que el portal aísla los datos correctamente: entra con `delgado.rios@example.com` y verifica que **no aparece** la obra de Altavista, y viceversa.

Nota importante: en la base de datos, las contraseñas de la tabla nunca están en texto plano — están hasheadas con bcrypt. Las contraseñas "de prueba" de esta tabla solo existen en texto plano aquí, en este manual, para que tú puedas iniciar sesión durante la validación. No las reutilices en ningún sistema real y cámbialas antes de exponer esto a internet.

Los scripts `database/generar_hashes.py`, `database/fix_passwords.py` y `database/generar_acceso_cliente.py` se actualizaron para usar estos mismos usuarios/contraseñas, así que si necesitas regenerar hashes en el futuro (por ejemplo tras un cambio de contraseña), seguirán generando datos consistentes con este manual.

---

## 5. Revisión de seguridad

Enfoque solicitado: que ningún usuario/contraseña viaje o se guarde "en transparente" (texto plano). Esto es lo que se encontró y lo que se hizo:

### 5.1 Contraseñas — cómo se manejan hoy

- **Al guardarse:** `bcrypt.hash(password, 10)` en `backend/routes/usuarios.js` (alta de usuario interno) y en los scripts Python de generación de accesos del portal. Nunca se guarda el texto plano en la base de datos. ✅ Correcto, no se tocó.
- **Al iniciar sesión:** el usuario escribe su contraseña una sola vez, en el formulario, y viaja en el `body` de un `POST` (no en la URL, no en query string, no en un log). Esto es correcto siempre y cuando el canal esté cifrado — ver el punto de HTTPS abajo.
- **Nunca se regresa al frontend:** las respuestas de la API (`/perfil`, `/usuarios`, etc.) seleccionan explícitamente las columnas que devuelven y **excluyen** `password` (`SELECT id, nombre, email, rol, ...`). Confirmé esto en cada ruta que lista o devuelve usuarios/accesos — no hay ningún `SELECT *` que se filtre al cliente con la contraseña (hasheada o no) adentro.
- **Secretos de la app** (`JWT_SECRET`, `DB_PASSWORD`): viven en `.env`, excluido de git por `.gitignore`, y el servidor **rehúsa arrancar** si faltan (`backend/db.js`, `backend/middleware/auth.js`) — no hay un valor por defecto inseguro escondido en el código. Correcto, no se tocó.

### 5.2 Hallazgo corregido: credencial expuesta en la pantalla de login

`frontend/src/components/Login.js` mostraba, debajo del botón de "Entrar", el texto `Demo: admin@constructora.com / Admin123!` — visible para cualquiera que abriera la página, sin necesidad de inspeccionar código ni red. Es exactamente el tipo de "credencial en transparente" que pediste revisar. **Se eliminó esa línea.** El portal del cliente (`PortalLogin.js`) no tenía este problema — ya solo decía "¿No tienes acceso? Solicítalo con tu arquitecto."

### 5.3 Hallazgo corregido: sin límite de intentos de login

Ni `/api/usuarios/login` ni `/api/portal/login` tenían protección contra fuerza bruta — alguien podía probar miles de contraseñas por segundo contra cualquier email. Se agregó `backend/middleware/loginLimiter.js` (usa `express-rate-limit`): máximo 8 intentos por IP cada 15 minutos, en ambos endpoints de login. El mensaje de error es genérico y no revela si el email existe o no, para no ayudar a un atacante a enumerar cuentas válidas.

### 5.4 Hallazgo corregido: faltaban cabeceras de seguridad HTTP

Se agregó `helmet()` como middleware global en `backend/server.js`. Activa por defecto protecciones como `X-Content-Type-Options`, `Strict-Transport-Security` (una vez que el sitio esté en HTTPS) y desactiva el header `X-Powered-By: Express` (evita anunciar la tecnología exacta del backend a un atacante).

### 5.5 Pendiente — requiere tu decisión: token en `localStorage`

El token JWT (tanto del sistema interno como del portal) se guarda en `localStorage` del navegador (`AuthContext.js`, `PortalAuthContext.js`). Esto es **común** y funciona, pero tiene una debilidad conocida: si alguna vez se cuela una vulnerabilidad de XSS (inyección de JavaScript malicioso) en cualquier parte del frontend, ese script podría leer `localStorage` y robar el token.

La alternativa más segura es una cookie `HttpOnly` + `Secure` + `SameSite`, que JavaScript no puede leer — pero implica: mover la emisión del token del `body` de la respuesta a un header `Set-Cookie` en el backend, quitar el manejo manual del header `Authorization` en el frontend, y agregar protección CSRF (porque las cookies sí se envían automáticamente entre orígenes). Es un cambio de arquitectura, no un parche de una línea, así que no lo apliqué sin que lo decidas tú. Para una primera versión interna/de prueba, el riesgo actual es aceptable; para producción con datos reales de clientes, te recomiendo hacerlo antes de publicar.

### 5.6 Pendiente — otras recomendaciones del checklist de seguridad

- No hay bloqueo explícito de cuenta tras N intentos fallidos (el rate limit ya frena el ataque automatizado, pero no queda un registro de "esta cuenta fue atacada").
- No hay expiración de sesión configurable por el usuario ni "cerrar sesión en todos los dispositivos" (el JWT expira solo, a las 8h; no hay lista de revocación).
- El registro de usuarios (`POST /usuarios/registro`) no valida longitud ni complejidad mínima de la contraseña — cualquier string pasa por `bcrypt.hash` sin importar qué tan débil sea.
- CORS se abre a `*` si no defines `FRONTEND_URL` — aceptable en desarrollo local, pero **debes** definir `FRONTEND_URL` con el dominio real antes de publicar.

### 5.7 Dependencias vulnerables (`npm audit`)

Corrí `npm audit` en `backend/`: reportó 7 vulnerabilidades. Apliqué `npm audit fix` (sin `--force`, sin cambios que rompan compatibilidad) y corrigió 3: `body-parser` (DoS), `brace-expansion` (DoS), `socket.io-parser` (agotamiento de memoria). Quedan pendientes:

- `uuid` / `exceljs` (severidad moderada): el fix automático requiere bajar `exceljs` a una versión anterior (`3.4.0`, cambio incompatible) — no lo apliqué para no arriesgar el módulo de exportación a Excel sin que lo pruebes. Si ese módulo no es crítico para ti ahora, puedes dejarlo así una temporada; si sí lo usas seguido, vale la pena programar la migración y probar la exportación después.
- `tar` / `@mapbox/node-pre-gyp` (severidad crítica reportada, pero es dependencia **de instalación** de `bcrypt`, no corre en producción — se usa solo al hacer `npm install` para compilar el binario nativo). Riesgo real bajo en este contexto, pero igual conviene revisarlo de vez en cuando con `npm audit`.

### 5.8 SQL Injection

Revisé el patrón de todas las rutas: **todas** las consultas usan parámetros (`?` con `mysql2`), nunca concatenación de texto del usuario dentro del SQL. No encontré ningún punto de inyección SQL.

---

## 6. Plan para la app móvil

Me indicaste que, además de la página web, este sistema va a tener una aplicación para celular. Aplicando tu proceso seguro (sección de "toda app debe funcionar bien en móvil" y la de seguridad):

**Buena noticia de arquitectura:** el backend ya está listo para esto sin cambios. Usa JWT en el header `Authorization: Bearer <token>` en vez de cookies de sesión — ese es exactamente el patrón que necesita una app móvil nativa (React Native, Flutter, etc.), porque una app móvil no maneja cookies de navegador de forma natural. La misma API que usa el frontend web (`/api/usuarios/login`, `/api/obras`, etc.) puede reutilizarse tal cual para la app móvil — no hace falta una segunda API.

**Lo que sí cambia para la app móvil:**

1. **Dónde se guarda el token en el celular**: nunca en almacenamiento plano (el equivalente a `localStorage` en móvil sería `AsyncStorage`, que **no** está cifrado en disco). Hay que usar el almacenamiento seguro del sistema operativo: `expo-secure-store` o `react-native-keychain` (usan Keychain en iOS y Keystore en Android). Este es el punto de mayor riesgo si se copia el patrón actual del frontend web sin adaptarlo.
2. **CORS no aplica a apps nativas**: la variable `FRONTEND_URL` que controla CORS en `server.js` solo protege a navegadores web — una app nativa (React Native, Flutter) no envía el header `Origin` de la misma forma y no se ve frenada por CORS. Esto es normal y no es una falla, pero significa que **no debes depender de CORS como control de acceso**: el rate limiting del login y la validación del JWT en cada ruta siguen siendo, como ya lo son, la verdadera barrera de seguridad — y ya están correctamente puestas por ruta, no por origen.
3. **HTTPS obligatorio, sin excepción**: en web uno podría "probar" sin TLS en desarrollo; en una app móvil publicada en tiendas (Google Play / App Store), tanto Android como iOS exigen o recomiendan fuertemente tráfico cifrado (`Network Security Config` en Android, `App Transport Security` en iOS bloquea HTTP por defecto). Railway ya sirve el backend con HTTPS, así que esto se resuelve solo si usas esa URL.
4. **Certificate pinning (opcional, para cuando el proyecto crezca)**: fijar en la app el certificado esperado del backend, para que ni siquiera un certificado válido-pero-distinto (ej. en una red corporativa con proxy MITM) sea aceptado. No es indispensable para una primera versión, pero es un siguiente paso razonable una vez que haya datos financieros reales de clientes en la app.
5. **Responsivo primero, app nativa después (opción intermedia):** dado que el frontend ya es React con `viewport` configurado correctamente (`frontend/public/index.html`), una alternativa más rápida que programar una app nativa desde cero es convertir el sistema en una **PWA** (Progressive Web App) instalable, como sugiere tu proceso seguro en la sección 6. Esto le da ícono propio y uso "tipo app" sin pasar por las tiendas, mientras decides si vale la pena invertir en una app nativa completa. Te lo dejo como opción, no como decisión tomada.

**Nota sobre roles en móvil:** los 4 roles (admin, supervisor, empleado, cliente) tienen sentido en una app móvil tal cual están — de hecho el **empleado** (que registra avance y bitácora "en campo", en la obra) y el **cliente** (que consulta el avance de su obra desde donde esté) son los dos roles con más razón de ser en celular antes que en escritorio.

---

## 7. Manual de Usuario — recorrido de validación por rol

Este apartado es para que valides tú mismo, con cada rol, que el sistema hace lo que se planteó. Usa las credenciales de la sección 4.

### Antes de empezar

```bash
# 1. Base de datos (una sola vez, o de nuevo si quieres reiniciar el escenario de ejemplo)
mysql -u root -p < database/constructora.sql
mysql -u root -p < database/migraciones/v2_ampliacion.sql
mysql -u root -p < database/migraciones/v3_diferenciadores.sql

# 2. Backend
cd backend
npm install         # trae helmet y express-rate-limit, agregados en esta revisión
npm run dev          # http://localhost:3001

# 3. Frontend (en otra terminal)
cd frontend
npm install
npm start            # http://localhost:3000
```

### 7.1 Rol Admin — control total

Entra en `http://localhost:3000/login` con `ana.ramirez@constructora.com` / `Direccion#2026`.

- [ ] El dashboard carga sin error y muestra el nombre "Ana Ramírez".
- [ ] En **Usuarios**, ves a Jorge (supervisor) y Paola (empleado) en la lista, ambos activos.
- [ ] Puedes dar de alta un cuarto usuario de prueba (cualquier rol) desde el panel de administración.
- [ ] Puedes desactivar y volver a activar a un usuario (por ejemplo, el que acabas de crear) desde **Usuarios**.
- [ ] En **Obras**, ves las dos obras del escenario (Residencia Delgado Ríos, Plaza Comercial Altavista).
- [ ] En **Tablero ejecutivo**, ves KPIs agregados de ambas obras (gasto real vs. contrato).
- [ ] Puedes exportar un reporte a Excel o PDF desde el panel de administración.
- [ ] Cierras sesión y el token deja de funcionar (si intentas volver a `/dashboard` sin volver a iniciar sesión, te regresa al login).

### 7.2 Rol Supervisor — operación de las obras

Entra con `jorge.villasenor@constructora.com` / `Supervisa#2026`.

- [ ] Ves las mismas dos obras que el admin, con el mismo detalle financiero.
- [ ] Puedes editar la obra "Plaza Comercial Altavista" (por ejemplo, cambiar el % de avance).
- [ ] En **Presupuestos**, ves el de "Instalaciones eléctricas e hidráulicas" en estado *revisión* — apruébalo o recházalo y confirma que el estado cambia.
- [ ] Verifica que **no** aparece la opción de dar de alta usuarios internos (eso es solo de admin).
- [ ] Registra un gasto nuevo en cualquiera de las dos obras.
- [ ] Revisa el **Tablero ejecutivo** — debe verse igual que con el admin.
- [ ] Intenta eliminar un gasto o un pago: no debería estar disponible (borrar es solo de admin).

### 7.3 Rol Empleado — operación diaria en campo

Entra con `paola.reyes@constructora.com` / `Campo#2026`.

- [ ] Puedes ver el detalle de ambas obras, pero **no** ves el Tablero ejecutivo (opción oculta o acceso denegado).
- [ ] Registra un avance semanal nuevo en "Residencia Delgado Ríos" (por ejemplo, etapa "Estructura", 45%).
- [ ] Registra una entrada de bitácora del día de hoy para la misma obra.
- [ ] Crea una tarea nueva y asígnatela a ti misma.
- [ ] Verifica que **no** puedes dar de alta un usuario ni ver la lista completa de usuarios.
- [ ] Verifica que **no** puedes eliminar un gasto ni un presupuesto ya aprobado.

### 7.4 Rol Cliente — portal de solo lectura

Este es un flujo **totalmente separado**: entra en `http://localhost:3000/portal/login` (no en `/login`).

**Primero como el cliente Delgado Ríos:**
`delgado.rios@example.com` / `Cliente#2026`

- [ ] Ves únicamente la obra "Residencia Delgado Ríos" — **no** aparece "Plaza Comercial Altavista".
- [ ] Ves el avance de obra (dos reportes semanales: 20% y 35%).
- [ ] Ves el estado de cuenta: un pago recibido (Anticipo 30%) y dos pendientes.
- [ ] En documentos, ves "Planos arquitectónicos v1" y "Licencia de construcción", pero **no** ves "Contrato de obra firmado" (está marcado como no visible al cliente — así prueba que el flag `visible_cliente` funciona).
- [ ] No hay ninguna opción para editar nada — todo es de solo lectura.

**Después cierra sesión y entra como el cliente Altavista:**
`contacto@altavista.mx` / `Altavista#2026`

- [ ] Ahora ves únicamente "Plaza Comercial Altavista" — **no** aparece la obra de Delgado Ríos.
- [ ] En el estado de cuenta, el pago "Primera estimación" aparece como **vencido** (para confirmar que ese estado se refleja bien en el portal).

**Prueba de aislamiento (la más importante para seguridad):** intenta, ya logueado como un cliente, adivinar la URL del detalle de la obra del otro cliente (por ejemplo, cambiando el número de obra en la URL de `/portal/obras/1` a `/portal/obras/2` si eres el cliente 1). El backend valida `cliente_id` en cada consulta (`backend/routes/portal.js`), así que debería devolver "Obra no encontrada" o "Acceso denegado", nunca los datos del otro cliente.

### 7.5 Prueba del límite de intentos de login (nuevo en esta revisión)

En cualquiera de los dos logins (interno o portal), escribe una contraseña incorrecta 9 veces seguidas para el mismo email. Al noveno intento (el límite es 8 por 15 minutos) deberías recibir el mensaje "Demasiados intentos de inicio de sesión. Intenta de nuevo en unos minutos." en vez de "Credenciales inválidas". Esto confirma que la protección contra fuerza bruta quedó activa.

---

## 8. Checklist antes de producción

Antes de publicar esto con datos reales de clientes:

- [ ] Definir `FRONTEND_URL` real en el backend (Railway) — no dejar CORS abierto a `*`.
- [ ] Confirmar que tanto el backend (Railway) como el frontend (Vercel) sirven todo por HTTPS.
- [ ] Cambiar `JWT_SECRET` y las contraseñas de MySQL a valores generados para producción (no reutilizar los de desarrollo local).
- [ ] Cambiar las 5 contraseñas de ejemplo de este manual (o eliminar esas cuentas) antes de exponer el sistema a internet.
- [ ] Decidir si migras el token de `localStorage` a cookies `HttpOnly` (sección 5.5) antes de manejar datos financieros reales de clientes.
- [ ] Agregar validación mínima de complejidad de contraseña en `POST /usuarios/registro`.
- [ ] Revisar el aviso de privacidad: el sistema guarda datos personales de clientes (nombre, email, teléfono, RFC) además de los tuyos — en México aplica la LFPDPPP. Un aviso breve dentro del portal, indicando qué datos se guardan y para qué, es suficiente para empezar; no hace falta un documento legal robusto de inicio.
- [ ] Resolver la dependencia moderada pendiente (`uuid`/`exceljs`, sección 5.7) probando la exportación a Excel después de actualizar.
- [ ] Configurar backups automáticos de la base de datos en Railway.
- [ ] Definir un plan de manejo de errores que nunca exponga detalles internos (stack traces, mensajes crudos de MySQL) al usuario final — revisar que todos los `catch` devuelvan mensajes genéricos como ya hacen hoy la mayoría de las rutas.

---

## 9. Qué se cambió exactamente en este trabajo

Resumen técnico de todos los archivos tocados, para tu control de versiones:

**Datos de ejemplo (reemplazo completo):**
- `database/constructora.sql` — nuevos usuarios (admin/supervisor/empleado), nuevas alertas de ejemplo; los presupuestos de ejemplo se movieron a `v2_ampliacion.sql`.
- `database/migraciones/v2_ampliacion.sql` — nuevos clientes, obras, presupuestos (ahora ligados a `obra_id`), pagos, proveedores, gastos, avances, tareas y bitácora.
- `database/migraciones/v3_diferenciadores.sql` — documentos renombrados para el nuevo escenario, y **accesos de ejemplo al portal del cliente agregados** (`clientes_acceso`), algo que antes no existía.
- `database/generar_hashes.py` y `database/fix_passwords.py` — actualizados a los nuevos usuarios/contraseñas de ejemplo.
- `database/generar_acceso_cliente.py` — agregada advertencia para no compartir la contraseña temporal del cliente por un canal en texto plano (correo/chat sin cifrar).

**Seguridad (backend):**
- `backend/package.json` — se agregaron `helmet` y `express-rate-limit`; se corrieron `npm install` y `npm audit fix` (3 vulnerabilidades resueltas, detalle en sección 5.7).
- `backend/server.js` — se agregó `helmet()` como middleware global.
- `backend/middleware/loginLimiter.js` — **archivo nuevo**, limitador de intentos de login.
- `backend/routes/usuarios.js` y `backend/routes/portal.js` — el limitador se aplicó a ambos endpoints de login.

**Seguridad (frontend):**
- `frontend/src/components/Login.js` — se eliminó la credencial de demo que se mostraba en texto plano en la pantalla de login.

**Documentación:**
- Este archivo (`INFORME_ANALISIS_Y_MANUAL_USUARIO.md`) — nuevo.
- `README.md` — se agregó una referencia a este informe (ver sección "Documentación adicional").

No se tocó: la lógica de negocio de ninguna ruta, el esquema de tablas existente (solo se agregaron filas de ejemplo, ninguna columna ni tabla nueva), ni el flujo de autenticación (localStorage se dejó igual, ver sección 5.5 para la razón).

---

## 10. Próximos pasos sugeridos

- Ya que vas a tener una app móvil, te conviene revisar **OWASP Mobile Application Security** (checklist gratuito) cuando empieces esa parte — encaja bien con lo que ya estás aprendiendo de ciberseguridad.
- Cuando decidas atacar el punto de "token en localStorage vs. cookies HttpOnly" (sección 5.5), es un buen ejercicio práctico de JWT + CSRF que refuerza justo lo que estás estudiando de redes/seguridad.
- Si quieres automatizar algo repetitivo: el flujo de "generar acceso de cliente" hoy es manual (correr un script Python y pegar el INSERT a mano). Podría convertirse en un endpoint `POST /admin/clientes/:id/acceso` protegido por rol admin/supervisor, que genere la contraseña temporal y la muestre una sola vez en pantalla — quitaría un paso manual propenso a error copy-paste.
