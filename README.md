# Sistema de Gestión — Constructora

Aplicación web fullstack para administrar la operación de una empresa constructora: obras, presupuestos, gastos, avances, cobros a clientes, proveedores, tareas, bitácora de obra, estimación de materiales, documentos y un portal de solo lectura para el cliente final, con alertas en tiempo real y control de acceso por rol.

📄 **Documentación adicional:** [`INFORME_ANALISIS_Y_MANUAL_USUARIO.md`](./INFORME_ANALISIS_Y_MANUAL_USUARIO.md) — análisis completo del sistema, matriz de permisos por rol, revisión de seguridad (manejo de contraseñas, límite de intentos de login, dependencias vulnerables), plan de la futura app móvil, y un manual de usuario paso a paso para validar los 4 roles (admin, supervisor, empleado, cliente/portal) con datos de ejemplo reales.

---

## Estado actual

**Funcional / en desarrollo activo.** El backend expone todos los módulos descritos abajo y el frontend los consume mediante rutas internas y un portal de cliente separado. No se encontraron pruebas automatizadas (no hay carpeta `tests` ni scripts `test` en los `package.json`), ni configuración de linting o CI. Es un proyecto apto para uso interno / demo, pero antes de producción conviene añadir pruebas, revisar los valores por defecto inseguros (ver "Notas relevantes") y endurecer el manejo de errores.

---

## Características principales

- **Gestión de obras**: alta de obras con cliente, tipo, responsable y monto de contrato; KPIs financieros (gasto real vs. contrato, saldo disponible).
- **Presupuestos** con flujo de estados (`borrador → revisión → aprobado / rechazado`).
- **Gastos reales** por obra, con resumen por categoría.
- **Avance de obra** semanal por etapa.
- **Pagos de cliente**: calendario de cobros, pagos pendientes/vencidos.
- **Proveedores y órdenes de compra**.
- **Tareas y bitácora diaria** de obra.
- **Tablero ejecutivo** con KPIs agregados de todas las obras activas.
- **Estimación de materiales**: catálogo de precios por categoría y calculadora que "congela" el precio al guardar una estimación.
- **Gestión documental** por obra, con versionado automático y control de visibilidad hacia el cliente.
- **Portal del cliente**: login y API independientes, de solo lectura, para que cada cliente consulte el estado de su obra, avance, estado de cuenta y documentos compartidos.
- **Alertas y eventos en tiempo real** vía Socket.io (nuevas alertas, cambios de presupuesto/obra, gastos registrados).
- **Control de acceso por rol** (admin, supervisor, empleado) mediante middleware de JWT + verificación de rol.
- **Exportación** de reportes a Excel y PDF (ExcelJS, PDFKit).

---

## Stack tecnológico

- **Backend**: Node.js + Express 4, MySQL2 (driver), Socket.io (tiempo real), JWT (`jsonwebtoken`) + bcrypt (autenticación), dotenv, ExcelJS y PDFKit (exportación). Servidor confirmado en `backend/server.js` y `backend/db.js`.
- **Frontend**: React 18 + React Router v6, Axios, Socket.io-client, Chart.js (`react-chartjs-2`), React Toastify. Bootstrapeado con `react-scripts` (Create React App).
- **Base de datos**: MySQL 8+ (esquema base en `database/constructora.sql` más dos migraciones incrementales).
- **Despliegue previsto**: Railway (backend + MySQL) y Vercel (frontend) — hay un `Procfile` (`web: node server.js`) preparado para plataformas tipo Heroku/Railway.

---

## Estructura del proyecto

```
04 proyecto-constructora/
├── backend/
│   ├── server.js            # Express + Socket.io, registro de rutas /api/*
│   ├── db.js                # Conexión MySQL (soporta variables DB_* y MYSQL* de Railway)
│   ├── middleware/
│   │   ├── auth.js          # Verificación de JWT
│   │   └── roles.js         # Control de acceso por rol
│   ├── routes/               # usuarios, obras, presupuestos, clientes, gastos, avance,
│   │                         # pagos, proveedores, tareas, bitacora, tablero,
│   │                         # estimaciones, documentos, portal, admin
│   └── package.json
├── frontend/
│   ├── public/
│   └── src/
│       ├── App.js, AuthContext.js, PortalAuthContext.js
│       ├── components/       # Dashboard, TableroEjecutivo, Obras, ObraDetalle,
│       │                     # Clientes, Proveedores, Presupuestos,
│       │                     # AlertasTiempoReal, PerfilUsuario, AdminPanel, Login
│       └── portal/           # PortalLogin, PortalObras, PortalObraDetalle (vista del cliente)
└── database/
    ├── constructora.sql               # Esquema base (usuarios, presupuestos, alertas)
    ├── migraciones/
    │   ├── v2_ampliacion.sql          # clientes, obras, gastos, avance_obra, pagos_cliente,
    │   │                              # proveedores, ordenes_compra, tareas, bitacora
    │   └── v3_diferenciadores.sql     # catalogo_materiales, estimaciones, estimacion_items,
    │                                  # documentos, clientes_acceso
    ├── generar_hashes.py              # Genera hashes bcrypt para usuarios de ejemplo
    ├── fix_passwords.py               # Utilidad para corregir contraseñas existentes
    └── generar_acceso_cliente.py      # Genera hash + INSERT para acceso del portal cliente
```

---

## Cómo instalar y ejecutar en local

### 1. Base de datos (MySQL 8+)

```bash
mysql -u root -p < database/constructora.sql
mysql -u root -p < database/migraciones/v2_ampliacion.sql
mysql -u root -p < database/migraciones/v3_diferenciadores.sql

# Genera hashes reales para las contraseñas de los usuarios de ejemplo
pip3 install bcrypt
python3 database/generar_hashes.py
# Copia el INSERT generado y reemplaza el que trae el SQL base
```

### 2. Backend

```bash
cd backend
cp .env.example .env
# Completa .env con tus credenciales de MySQL y un JWT_SECRET propio
npm install
npm run dev      # con nodemon, o "npm start" para producción
# Servidor en http://localhost:3001
```

### 3. Frontend

```bash
cd frontend
npm install
npm start
# App en http://localhost:3000 (usa el proxy definido en package.json hacia el backend)
```

### 4. Acceso al portal del cliente

El acceso de un cliente al portal se crea manualmente:

```bash
python3 database/generar_acceso_cliente.py
```

Esto genera el hash bcrypt y el `INSERT` para la tabla `clientes_acceso`.

---

## Notas relevantes

- **Variables de entorno del backend** (`backend/.env`, ver `backend/.env.example`): `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `JWT_SECRET`, `PORT`. En despliegues sobre Railway, `db.js` también acepta las variables inyectadas automáticamente `MYSQLHOST`, `MYSQLUSER`, `MYSQLPASSWORD`, `MYSQLDATABASE`, `MYSQLPORT`.
- **Variable de entorno del frontend** (`frontend/.env.example`): `REACT_APP_API_URL`, solo necesaria en producción; en local el proxy de `package.json` redirige `/api` a `http://localhost:3001`.
- **Variables obligatorias**: `DB_PASSWORD` (o `MYSQLPASSWORD`) y `JWT_SECRET` ya no tienen un *fallback* hardcodeado — `backend/db.js`, `backend/middleware/auth.js`, `backend/routes/usuarios.js` y `backend/routes/portal.js` lanzan un error al arrancar si no están definidas. Configúralas siempre en `.env` (ver `backend/.env.example`) antes de iniciar el servidor.
- **Sin almacenamiento binario de archivos**: el módulo de documentos guarda solo la referencia (`url_archivo`); se recomienda integrarlo con un servicio externo (S3, Google Drive, disco del servidor) para el archivo real.
- **Sin pruebas automatizadas**: no se detectaron suites de test en backend ni frontend.
- **CORS y Socket.io** están controlados por la variable `FRONTEND_URL`; si no se define, se abre a cualquier origen (`*`), lo cual es aceptable solo en desarrollo local.
- **No copiar contraseñas reales**: los archivos `.env` están correctamente excluidos en `.gitignore` (`.env`, `*/.env`); usa siempre `.env.example` como referencia de las variables requeridas.
- **Seguridad de login**: `POST /api/usuarios/login` y `POST /api/portal/login` tienen un límite de 8 intentos por IP cada 15 minutos (`backend/middleware/loginLimiter.js`, agregado junto con `helmet` en la revisión de seguridad de 2026-08-21 — detalle completo en `INFORME_ANALISIS_Y_MANUAL_USUARIO.md`).
- **Contraseñas de ejemplo**: las credenciales de prueba (admin/supervisor/empleado/portal) que trae el proyecto están documentadas únicamente en `INFORME_ANALISIS_Y_MANUAL_USUARIO.md` — cámbialas o elimina esas cuentas antes de exponer el sistema a internet.
