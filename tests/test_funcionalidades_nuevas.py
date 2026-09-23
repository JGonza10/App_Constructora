import io
from datetime import date, timedelta
from decimal import Decimal

from constructora.extensions import db
from constructora.models import (
    Obra, Cliente, ClienteAcceso, ConceptoCatalogo, PagoCliente, Documento, BitacoraFoto,
)
from constructora.tareas_programadas import marcar_pagos_vencidos

from .conftest import login
from .test_flujo_completo import _crear_obra_via_flujo


def test_catalogo_crud_y_se_usa_en_form_cotizacion(client, admin):
    login(client, "admin@example.com", "Password123!")
    resp = client.post("/catalogo/nuevo", data={
        "concepto": "Excavación", "unidad": "m3", "precio_unitario": "850", "categoria": "Cimentación",
    }, follow_redirects=False)
    assert resp.status_code == 302
    concepto = ConceptoCatalogo.query.filter_by(concepto="Excavación").first()
    assert concepto is not None

    resp = client.get("/catalogo/")
    assert resp.status_code == 200
    assert b"Excavaci\xc3\xb3n" in resp.data

    obra = _crear_obra_via_flujo(client, "Cliente Catálogo", cantidad=1, precio_unitario=1)
    from constructora.models import Levantamiento
    levantamiento = Levantamiento.query.filter_by(cliente_id=obra.cliente_id).first()
    resp = client.get(f"/cotizaciones/levantamiento/{levantamiento.id}/nueva")
    assert resp.status_code == 200
    assert b"selector-catalogo" in resp.data


def test_pdf_cotizacion_se_genera(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente PDF", cantidad=2, precio_unitario=500)
    resp = client.get(f"/cotizaciones/{obra.cotizacion_id}/pdf")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data[:4] == b"%PDF"


def test_comparar_versiones_cotizacion(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Comparar", cantidad=1, precio_unitario=100)
    levantamiento_id = obra.cotizacion.levantamiento_id
    resp = client.get(f"/cotizaciones/levantamiento/{levantamiento_id}/comparar")
    assert resp.status_code == 200


def test_alerta_presupuesto_marca_nivel_al_cruzar_90_porciento(client, admin, app):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Presupuesto", cantidad=1, precio_unitario=1000)
    assert obra.nivel_alerta_presupuesto == 0

    client.post(f"/obras/{obra.id}/gastos/nuevo", data={
        "categoria": "materiales", "concepto": "Material caro", "cantidad": "1",
        "unidad": "pza", "monto": "950", "fecha": "2026-03-01", "proveedor_id": "0",
    }, follow_redirects=False)

    db.session.refresh(obra)
    assert obra.nivel_alerta_presupuesto == 90


def test_marcar_pagos_vencidos_cambia_estado(app, admin):
    with app.app_context():
        cliente = Cliente(nombre="Cliente Vencido", tipo="persona_fisica")
        db.session.add(cliente)
        db.session.commit()
        from constructora.models import Levantamiento, Cotizacion, CotizacionItem
        lev = Levantamiento(cliente_id=cliente.id, titulo="Obra X", tipo_obra="residencial", indicaciones_cliente="x")
        db.session.add(lev)
        db.session.commit()
        cot = Cotizacion(levantamiento_id=lev.id, version=1, titulo="v1", estado="aceptada")
        cot.items = [CotizacionItem(concepto="c", unidad="pza", cantidad=1, precio_unitario=100)]
        db.session.add(cot)
        db.session.commit()
        obra = Obra(cotizacion_id=cot.id, cliente_id=cliente.id, nombre="Obra X", tipo="residencial", monto_contrato=cot.total)
        db.session.add(obra)
        db.session.commit()

        pago = PagoCliente(
            obra_id=obra.id, concepto="Anticipo", monto=100,
            fecha_programada=date.today() - timedelta(days=3), estado="pendiente",
        )
        db.session.add(pago)
        db.session.commit()

        n = marcar_pagos_vencidos()
        assert n == 1
        db.session.refresh(pago)
        assert pago.estado == "vencido"


def test_documento_con_archivo_subido_y_descarga(client, admin, app, tmp_path):
    app.instance_path = str(tmp_path)
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Documento", cantidad=1, precio_unitario=100)

    data = {
        "nombre": "Plano de prueba", "categoria": "plano",
        "archivo": (io.BytesIO(b"contenido falso de pdf"), "plano.pdf"),
        "url_archivo": "", "visible_cliente": "y",
    }
    resp = client.post(f"/obras/{obra.id}/documentos/nuevo", data=data,
                        content_type="multipart/form-data", follow_redirects=False)
    assert resp.status_code == 302

    doc = Documento.query.filter_by(obra_id=obra.id).first()
    assert doc.url_archivo.startswith("local:documentos/")

    resp = client.get(f"/obras/{obra.id}/documentos/{doc.id}/descargar")
    assert resp.status_code == 200
    assert resp.data == b"contenido falso de pdf"


def test_bitacora_con_foto_subida(client, admin, app, tmp_path):
    app.instance_path = str(tmp_path)
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Bitácora", cantidad=1, precio_unitario=100)

    data = {
        "fecha": "2026-03-05", "clima": "soleado", "personal_en_obra": "5",
        "actividades": "Colado", "incidencias": "",
        "fotos": [(io.BytesIO(b"imagen falsa"), "foto1.jpg")],
    }
    resp = client.post(f"/obras/{obra.id}/bitacora/nueva", data=data,
                        content_type="multipart/form-data", follow_redirects=False)
    assert resp.status_code == 302

    foto = BitacoraFoto.query.first()
    assert foto is not None
    resp = client.get(f"/obras/{obra.id}/bitacora/fotos/{foto.id}")
    assert resp.status_code == 200


def test_reporte_cierre_y_nomina_semanal(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Reporte", cantidad=1, precio_unitario=1000)
    resp = client.get(f"/obras/{obra.id}/reporte-cierre")
    assert resp.status_code == 200

    resp = client.get("/trabajadores/nomina")
    assert resp.status_code == 200


def test_portal_cliente_acepta_cotizacion_y_nace_la_obra(client, admin):
    login(client, "admin@example.com", "Password123!")
    resp = client.post("/clientes/nuevo", data={
        "nombre": "Cliente Portal Acepta", "tipo": "persona_fisica",
        "email": "", "telefono": "", "rfc": "", "direccion": "", "notas": "",
    }, follow_redirects=False)
    cliente = Cliente.query.filter_by(nombre="Cliente Portal Acepta").first()

    client.post("/levantamientos/nuevo", data={
        "cliente_id": str(cliente.id), "titulo": "Proyecto Portal",
        "tipo_obra": "residencial", "direccion": "Calle 1",
        "indicaciones_cliente": "Indicaciones",
    }, follow_redirects=False)
    from constructora.models import Levantamiento, Cotizacion
    levantamiento = Levantamiento.query.filter_by(cliente_id=cliente.id).first()

    client.post(f"/cotizaciones/levantamiento/{levantamiento.id}/nueva", data={
        "titulo": "Cotización portal", "notas": "",
        "items-0-concepto": "Concepto", "items-0-unidad": "pza",
        "items-0-cantidad": "1", "items-0-precio_unitario": "5000",
    }, follow_redirects=False)
    cotizacion = Cotizacion.query.filter_by(levantamiento_id=levantamiento.id).first()
    client.post(f"/cotizaciones/{cotizacion.id}/enviar", follow_redirects=False)
    client.get("/logout")

    acceso = ClienteAcceso(cliente_id=cliente.id, email="acepta@example.com")
    acceso.set_password("PortalPass1!")
    db.session.add(acceso)
    db.session.commit()

    login(client, "acepta@example.com", "PortalPass1!", portal=True)
    resp = client.get(f"/portal/cotizaciones/{cotizacion.id}")
    assert resp.status_code == 200

    resp = client.post(f"/portal/cotizaciones/{cotizacion.id}/aceptar", follow_redirects=False)
    assert resp.status_code == 302

    db.session.refresh(cotizacion)
    assert cotizacion.estado == "aceptada"
    obra = Obra.query.filter_by(cotizacion_id=cotizacion.id).first()
    assert obra is not None
    assert obra.monto_contrato == Decimal("5000.00")
