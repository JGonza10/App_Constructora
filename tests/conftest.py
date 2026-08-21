import os

os.environ.setdefault("SECRET_KEY", "clave-de-pruebas-no-usar-en-produccion")
os.environ.setdefault("DB_PASSWORD", "no-se-usa-porque-los-tests-corren-en-sqlite")

import pytest

from config import TestConfig
from constructora import create_app
from constructora.extensions import db as _db
from constructora.models import Usuario


@pytest.fixture()
def app():
    flask_app = create_app(TestConfig)
    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def admin(app):
    usuario = Usuario(nombre="Admin de prueba", email="admin@example.com", rol="admin")
    usuario.set_password("Password123!")
    _db.session.add(usuario)
    _db.session.commit()
    return usuario


def login(client, email, password, portal=False):
    url = "/portal/login" if portal else "/login"
    return client.post(url, data={"email": email, "password": password}, follow_redirects=True)
