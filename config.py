import os


def _requerido(nombre):
    valor = os.environ.get(nombre)
    if not valor:
        raise RuntimeError(
            f"Falta configurar {nombre} en las variables de entorno. "
            f"Copia .env.example a .env y define un valor real antes de iniciar la app."
        )
    return valor


class Config:
    SECRET_KEY = _requerido("SECRET_KEY")

    _db_host = os.environ.get("DB_HOST") or os.environ.get("MYSQLHOST") or "localhost"
    _db_port = os.environ.get("DB_PORT") or os.environ.get("MYSQLPORT") or "3306"
    _db_user = os.environ.get("DB_USER") or os.environ.get("MYSQLUSER") or "root"
    _db_password = os.environ.get("DB_PASSWORD") or os.environ.get("MYSQLPASSWORD")
    _db_name = os.environ.get("DB_NAME") or os.environ.get("MYSQLDATABASE") or "constructora"

    if not _db_password:
        raise RuntimeError(
            "Falta configurar DB_PASSWORD (o MYSQLPASSWORD) en las variables de entorno."
        )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{_db_name}"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"

    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB por archivo subido (documentos/fotos)


class TestConfig:
    """Config para pytest: SQLite en memoria, sin depender de MySQL ni de .env."""
    SECRET_KEY = "clave-de-pruebas-no-usar-en-produccion"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
