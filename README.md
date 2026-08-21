# Sistema de Gestión — Constructora

Aplicación web (Python/Flask, monolítica) para administrar la operación de una empresa constructora, con un flujo obligatorio que refleja cómo se trabaja en la vida real:

**Cliente → Levantamiento (qué pidió) → Cotización (versionable) → al aceptarse, nace la Obra → todo lo que pasa en campo (gastos de materiales, pagos de mano de obra por oficio, avance, tareas, bitácora, documentos, pagos del cliente) queda ligado únicamente a esa obra.**

No hay botón para "crear una obra" directamente — nace sola cuando se acepta una cotización, con el monto de contrato heredado de ahí (nunca se vuelve a teclear a mano). Cada formulario, al guardarse, ofrece el siguiente paso lógico en vez de dejarte adivinar a dónde ir.

📄 **Documentación adicional:** [`INFORME_ANALISIS_Y_MANUAL_USUARIO.md`](./INFORME_ANALISIS_Y_MANUAL_USUARIO.md) — diagnóstico del sistema anterior, diseño del flujo nuevo, revisión de seguridad y manual de usuario por rol.

---

## Roles

- **admin** — control total, incluye alta de usuarios internos.
- **supervisor** — gestiona clientes, levantamientos, cotizaciones (aceptar/rechazar), obras.
- **empleado** — captura operación de campo: gastos, mano de obra, avance, bitácora, tareas.
- **cliente (portal)** — login aparte, de solo lectura, ve únicamente su(s) obra(s): avance, estado de cuenta, documentos marcados como visibles.

---

## Stack tecnológico

- **Backend + frontend**: Python 3 + Flask (monolítico, sin API separada) — Jinja2 + Bootstrap 5 para las plantillas, responsivo de fábrica.
- **Base de datos**: MySQL 8+, vía SQLAlchemy (`Flask-SQLAlchemy`) + `PyMySQL`.
- **Auth**: `Flask-Login` con sesiones de cookie `HttpOnly`/`Secure` (no JWT en `localStorage`), contraseñas con `Flask-Bcrypt`, `Flask-WTF` para CSRF, `Flask-Limiter` contra fuerza bruta en los dos logins (interno y portal).
- **Despliegue**: Railway — un servicio Python (Gunicorn) + un servicio MySQL, en el mismo proyecto, conectado al repo de GitHub.

---

## Estructura del proyecto

```
04 proyecto-constructora/
├── config.py                # Config (producción) y TestConfig (SQLite en memoria)
├── wsgi.py                  # punto de entrada (gunicorn wsgi:app)
├── seed.py                  # recrea el esquema y carga datos de ejemplo de los 4 roles
├── requirements.txt
├── constructora/
│   ├── __init__.py          # app factory, blueprints, manejo de errores, `flask init-db`
│   ├── extensions.py        # db, bcrypt, csrf, login_manager, limiter
│   ├── models.py            # todo el esquema (SQLAlchemy)
│   ├── forms.py             # formularios WTForms
│   ├── decorators.py        # roles_requeridos(), solo_cliente_portal()
│   ├── auth.py               # login/logout interno
│   ├── portal.py             # login/logout + vistas de solo lectura del cliente
│   ├── main.py                # dashboard
│   ├── clientes.py, levantamientos.py, cotizaciones.py, obras.py,
│   │   trabajadores.py, usuarios.py   # un blueprint por dominio
│   └── templates/            # Jinja2 + Bootstrap 5
└── tests/                    # pytest — flujo completo, aislamiento por obra y por cliente
```

---

## Cómo instalar y ejecutar en local

```bash
# 1. Entorno virtual e instalación
python -m venv venv
venv\Scripts\activate          # Windows (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt

# 2. Variables de entorno
copy .env.example .env         # define SECRET_KEY, DB_* con tus datos de MySQL local
# En local (HTTP, sin TLS) deja SESSION_COOKIE_SECURE=false en .env

# 3. Base de datos — dos opciones
python -m flask --app wsgi init-db     # crea las tablas, sin datos de ejemplo
# — o, para un escenario de prueba completo con los 4 roles —
python seed.py                          # OJO: borra y recrea todo el esquema

# 4. Levantar la app
python wsgi.py
# http://localhost:5000
```

### Pruebas

```bash
pytest tests/ -v
```

Corren contra SQLite en memoria (`config.TestConfig`), no requieren MySQL.

---

## Notas relevantes

- **Variables de entorno** (ver `.env.example`): `SECRET_KEY`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SESSION_COOKIE_SECURE`. La app **no arranca** si falta `SECRET_KEY` o `DB_PASSWORD` — no hay valores por defecto inseguros.
- **`seed.py` es destructivo**: borra todas las tablas antes de recrear el escenario de ejemplo. Está pensado para desarrollo local y para la primera carga de datos de demo — nunca correrlo contra una base con datos reales de clientes.
- **Sin almacenamiento binario de archivos**: el módulo de documentos guarda solo la referencia (`url_archivo`); falta integrarlo con un servicio externo (S3, disco, etc.) para el archivo real.
- **Pruebas automatizadas**: sí existen (`tests/`), cubren el flujo cliente→levantamiento→cotización→obra, el aislamiento de datos entre obras, y el aislamiento del portal entre clientes. No hay cobertura de exportación de reportes ni de otros módulos de "fase 2" (ver el informe) porque todavía no existen.
- **No copiar contraseñas reales**: `.env` está excluido en `.gitignore`; usa siempre `.env.example` como referencia.
