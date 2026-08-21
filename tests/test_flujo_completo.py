from decimal import Decimal

from constructora.extensions import db
from constructora.models import Obra, ClienteAcceso, Cliente

from .conftest import login


def _crear_obra_via_flujo(client, nombre_cliente, cantidad, precio_unitario):
    """Recorre el flujo real (cliente -> levantamiento -> cotizacion -> obra)
    tal como lo haria un usuario, y regresa el id de la obra creada."""
    resp = client.post("/clientes/nuevo", data={
        "nombre": nombre_cliente, "tipo": "persona_fisica",
        "email": "", "telefono": "", "rfc": "", "direccion": "", "notas": "",
    }, follow_redirects=False)
    assert resp.status_code == 302
    cliente = Cliente.query.filter_by(nombre=nombre_cliente).first()
    assert cliente is not None

    resp = client.post("/levantamientos/nuevo", data={
        "cliente_id": str(cliente.id), "titulo": f"Obra de {nombre_cliente}",
        "tipo_obra": "residencial", "direccion": "Calle Falsa 123",
        "indicaciones_cliente": "El cliente pidió una remodelación completa.",
    }, follow_redirects=False)
    assert resp.status_code == 302

    from constructora.models import Levantamiento
    levantamiento = Levantamiento.query.filter_by(cliente_id=cliente.id).first()

    resp = client.post(f"/cotizaciones/levantamiento/{levantamiento.id}/nueva", data={
        "titulo": "Cotización inicial", "notas": "",
        "items-0-concepto": "Concreto premezclado", "items-0-unidad": "m3",
        "items-0-cantidad": str(cantidad), "items-0-precio_unitario": str(precio_unitario),
    }, follow_redirects=False)
    assert resp.status_code == 302

    from constructora.models import Cotizacion
    cotizacion = Cotizacion.query.filter_by(levantamiento_id=levantamiento.id).first()
    assert cotizacion.estado == "borrador"

    client.post(f"/cotizaciones/{cotizacion.id}/enviar", follow_redirects=False)
    db.session.refresh(cotizacion)
    assert cotizacion.estado == "enviada"

    resp = client.post(f"/cotizaciones/{cotizacion.id}/aceptar", data={
        "responsable_id": "0", "fecha_inicio": "", "fecha_fin_estimada": "",
    }, follow_redirects=False)
    assert resp.status_code == 302

    obra = Obra.query.filter_by(cotizacion_id=cotizacion.id).first()
    assert obra is not None
    return obra


def test_login_admin_funciona(client, admin):
    resp = login(client, "admin@example.com", "Password123!")
    assert resp.status_code == 200
    assert "Hola, Admin".encode() in resp.data


def test_login_con_password_incorrecta_falla(client, admin):
    resp = login(client, "admin@example.com", "clave-equivocada")
    assert b"Credenciales inv\xc3\xa1lidas" in resp.data


def test_flujo_cliente_a_obra_hereda_monto_de_la_cotizacion(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente de Prueba", cantidad=10, precio_unitario=100)
    assert obra.monto_contrato == Decimal("1000.00")
    assert obra.estado == "activa"

    resp = client.get(f"/obras/{obra.id}")
    assert resp.status_code == 200
    assert obra.nombre.encode() in resp.data


def test_gasto_y_pago_mano_obra_quedan_ligados_solo_a_su_obra(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra_a = _crear_obra_via_flujo(client, "Cliente A", cantidad=5, precio_unitario=200)
    obra_b = _crear_obra_via_flujo(client, "Cliente B", cantidad=5, precio_unitario=200)

    client.post(f"/obras/{obra_a.id}/gastos/nuevo", data={
        "categoria": "materiales", "concepto": "Cemento", "cantidad": "10",
        "unidad": "pza", "monto": "500", "fecha": "2026-03-01", "proveedor_id": "0",
    }, follow_redirects=False)

    db.session.refresh(obra_a)
    db.session.refresh(obra_b)
    assert len(obra_a.gastos) == 1
    assert len(obra_b.gastos) == 0

    from constructora.models import Trabajador
    trabajador = Trabajador(nombre="Juan Pérez", oficio="albanil", tipo_pago="por_dia")
    db.session.add(trabajador)
    db.session.commit()

    client.post(f"/obras/{obra_a.id}/mano-de-obra/nuevo", data={
        "trabajador_id": str(trabajador.id), "concepto": "Día de trabajo",
        "dias_o_unidades": "1", "monto": "400", "fecha": "2026-03-01",
    }, follow_redirects=False)

    db.session.refresh(obra_a)
    db.session.refresh(obra_b)
    assert len(obra_a.pagos_mano_obra) == 1
    assert len(obra_b.pagos_mano_obra) == 0
    assert obra_a.gasto_real == Decimal("900.00")


def test_portal_cliente_no_ve_obras_de_otro_cliente(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra_a = _crear_obra_via_flujo(client, "Cliente Portal A", cantidad=1, precio_unitario=1000)
    obra_b = _crear_obra_via_flujo(client, "Cliente Portal B", cantidad=1, precio_unitario=1000)
    client.get("/logout")

    acceso_a = ClienteAcceso(cliente_id=obra_a.cliente_id, email="portal.a@example.com")
    acceso_a.set_password("PortalPass1!")
    db.session.add(acceso_a)
    db.session.commit()

    login(client, "portal.a@example.com", "PortalPass1!", portal=True)

    resp = client.get(f"/portal/obras/{obra_a.id}")
    assert resp.status_code == 200

    resp = client.get(f"/portal/obras/{obra_b.id}")
    assert resp.status_code == 404
