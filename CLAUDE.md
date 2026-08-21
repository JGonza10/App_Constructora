# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es esto

Aplicación web fullstack para administrar la operación de una empresa constructora: obras, presupuestos, gastos, avance de obra, cobros a clientes, proveedores, tareas, bitácora, estimación de materiales, documentos por obra y un portal de solo lectura separado para el cliente final. Backend Node.js/Express + MySQL, frontend React. Todo el dominio, rutas y mensajes están en español — sigue esa convención.

Sin pruebas automatizadas, sin linter ni CI configurados. Estado: funcional/en desarrollo, no endurecido para producción (ver `README.md`, sección "Estado actual" y "Notas relevantes" — no las repito aquí).

## Comandos

**Base de datos (MySQL 8+)**, en orden — el esquema no usa un ORM con migraciones automáticas, hay que aplicar los tres archivos SQL a mano:
```bash
mysql -u root -p < database/constructora.sql
mysql -u root -p < database/migraciones/v2_ampliacion.sql
mysql -u root -p < database/migraciones/v3_diferenciadores.sql
```

**Backend** (`backend/`, Express 4 + Socket.io):
```bash
cd backend
cp .env.example .env   # define DB_* y JWT_SECRET — el servidor NO arranca sin ellos (ver abajo)
npm install
npm run dev             # nodemon, puerto 3001
npm start                # producción (node server.js)
```

**Frontend** (`frontend/`, Create React App):
```bash
cd frontend
npm install
npm start   # puerto 3000; proxy de package.json redirige /api -> http://localhost:3001, no hace falta configurar REACT_APP_API_URL en local
```

No hay `npm test` real configurado en ninguno de los dos `package.json` (frontend no incluye el script `test` de CRA, backend no tiene scripts de test).

## Arquitectura

- **`backend/server.js`** — único punto de entrada Express. Registra un router por dominio bajo `/api/<recurso>` (usuarios, presupuestos, admin, clientes, obras, gastos, avance, pagos, proveedores, tareas, bitacora, tablero, estimaciones, documentos, portal) más `/api/health`. Cada request recibe `req.io` (instancia de Socket.io) inyectado por middleware para que las rutas puedan emitir eventos en tiempo real (`alerta_recibida`, `presupuesto_cambio`, `obra_cambio`, `gasto_nuevo`) sin importar Socket.io en cada archivo de ruta.
- **Auth**: `backend/middleware/auth.js` (`verificarToken`) exige `Authorization: Bearer <jwt>`, firmado con `JWT_SECRET`; **lanza excepción al cargar el módulo si `JWT_SECRET` no está definido** — no hay fallback inseguro. `backend/middleware/roles.js` (`verificarRol(...roles)`) es un factory que compone con `verificarToken` en las rutas (`req.usuario.rol` debe estar en la lista); roles: `admin`, `supervisor`, `empleado`. `backend/middleware/loginLimiter.js` (`express-rate-limit`, 8 intentos / 15 min por IP) está aplicado en `POST /api/usuarios/login` y `POST /api/portal/login` — si agregas otro endpoint de login (ej. para la futura app móvil), aplícale el mismo limitador. `helmet()` está activo como middleware global en `server.js`.
- **Portal del cliente** (`routes/portal.js`) es un sistema de auth y datos **separado** del admin/empleado — login propio, solo lectura, contra la tabla `clientes_acceso`. El acceso de cada cliente se crea manualmente corriendo `database/generar_acceso_cliente.py` (genera el hash bcrypt + INSERT), no hay flujo de alta desde la UI.
- **Base de datos**: `database/constructora.sql` es el esquema base (usuarios, presupuestos, alertas); `migraciones/v2_ampliacion.sql` agrega el dominio de negocio principal (clientes, obras, gastos, avance_obra, pagos_cliente, proveedores, ordenes_compra, tareas, bitacora); `migraciones/v3_diferenciadores.sql` agrega catalogo_materiales, estimaciones/estimacion_items, documentos, clientes_acceso. Si agregas una tabla nueva, sigue el patrón de migración incremental numerada (`vN_*.sql`) en vez de editar el esquema base.
- **Estimación de materiales**: la calculadora "congela" el precio del catálogo al momento de guardar una estimación (no recalcula si el catálogo cambia después) — respeta ese comportamiento si tocas `routes/estimaciones.js`.
- **Documentos**: el módulo solo guarda la referencia (`url_archivo`) en la tabla `documentos`, con versionado y un flag de visibilidad hacia el portal del cliente; no hay almacenamiento binario propio, se asume un servicio externo (S3, disco, etc.) para el archivo real.
- **Tiempo real**: `server.js` expone eventos genéricos de Socket.io (`unirse_sala` por rol, y los cuatro eventos de dominio arriba). El frontend los consume en `AlertasTiempoReal` y otros componentes vía `socket.io-client`.
- **Despliegue previsto**: Railway para backend+MySQL (`db.js` acepta tanto `DB_*` como las variables `MYSQL*`/`MYSQLHOST` etc. que inyecta Railway automáticamente) y Vercel para el frontend; hay `Procfile` (`web: node server.js`).
- **CORS/Socket.io**: controlados por `FRONTEND_URL`; si no está definida, se abre a cualquier origen (`*`) — aceptable solo en desarrollo local, no lo dejes así en un despliegue real. Ojo: CORS solo frena navegadores web — no protege contra una app móvil nativa ni contra un cliente HTTP directo (curl, Postman); la verdadera barrera de acceso es `verificarToken`/`verificarRol` en cada ruta, no CORS.
- **App móvil planeada**: además del frontend web, está previsto construir una app móvil (nativa o PWA) consumiendo esta misma API — el diseño de auth con JWT en header `Authorization` (en vez de cookies) ya es compatible con eso sin cambios en el backend. Si implementas la app, el token debe guardarse en almacenamiento seguro del SO (`expo-secure-store` / `react-native-keychain`), nunca en `AsyncStorage` plano. Detalle completo en `INFORME_ANALISIS_Y_MANUAL_USUARIO.md`, sección 6.
- **Datos de ejemplo**: los usuarios/clientes/obras de prueba se reescribieron por completo el 2026-08-21 (ver `INFORME_ANALISIS_Y_MANUAL_USUARIO.md`). Si necesitas regenerar hashes de contraseñas de ejemplo, `database/generar_hashes.py`, `database/fix_passwords.py` y `database/generar_acceso_cliente.py` ya están alineados con ese mismo escenario — no reintroduzcas los usuarios viejos (`admin@constructora.com`, etc.), ya no existen.
