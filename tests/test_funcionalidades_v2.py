import io
from datetime import date, timedelta
from decimal import Decimal

from constructora.extensions import db
from constructora.models import (
    Obra, Trabajador, Equipo, Subcontratista, PlantillaCotizacion, PlantillaItem,
    MovimientoInventario, OrdenCompra, OrdenCambio, IncidenteSeguridad, Asistencia,
    AusenciaTrabajador, DocumentoTrabajador, MensajeObra, RegistroAuditoria, Documento,
    ContratoSubcontratista, AsignacionEquipo, Cotizacion, ClienteAcceso,
)
from constructora.tareas_programadas import avisar_documentos_por_vencer

from .conftest import login
from .test_flujo_completo import _crear_obra_via_flujo


def test_inventario_entradas_y_salidas(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Inventario", cantidad=1, precio_unitario=1000)

    client.post(f"/obras/{obra.id}/inventario/nuevo", data={
        "tipo": "entrada", "material": "Cemento", "unidad": "saco", "cantidad": "50",
        "motivo": "Compra inicial", "fecha": "2026-03-01",
    })
    client.post(f"/obras/{obra.id}/inventario/nuevo", data={
        "tipo": "salida", "material": "Cemento", "unidad": "saco", "cantidad": "20",
        "motivo": "Consumo semana 1", "fecha": "2026-03-05",
    })
    db.session.refresh(obra)
    resumen = obra.inventario_resumen()
    assert resumen["Cemento (saco)"] == 30.0


def test_orden_compra_recibir_genera_gasto_e_inventario(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Compras", cantidad=1, precio_unitario=1000)

    client.post(f"/obras/{obra.id}/compras/nueva", data={
        "proveedor_id": "0", "concepto": "Varilla 3/8", "cantidad": "100", "unidad": "pza",
        "costo_estimado": "5000", "fecha_solicitud": "2026-03-01",
    })
    orden = OrdenCompra.query.filter_by(obra_id=obra.id).first()
    assert orden.estado == "solicitada"

    client.post(f"/obras/{obra.id}/compras/{orden.id}/confirmar")
    db.session.refresh(orden)
    assert orden.estado == "confirmada"

    client.post(f"/obras/{obra.id}/compras/{orden.id}/recibir")
    db.session.refresh(orden)
    assert orden.estado == "recibida"
    assert orden.gasto_generado_id is not None
    assert MovimientoInventario.query.filter_by(obra_id=obra.id, tipo="entrada").count() == 1


def test_orden_cambio_aprobada_sube_monto_contrato_y_audita(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Cambios", cantidad=1, precio_unitario=1000)
    monto_original = obra.monto_contrato

    client.post(f"/obras/{obra.id}/cambios/nueva", data={
        "descripcion": "Cliente pidió agregar una recámara", "monto": "50000",
    })
    orden = OrdenCambio.query.filter_by(obra_id=obra.id).first()

    client.post(f"/obras/{obra.id}/cambios/{orden.id}/resolver", data={"decision": "aprobada"})
    db.session.refresh(obra)
    db.session.refresh(orden)
    assert orden.estado == "aprobada"
    assert obra.monto_contrato == monto_original + Decimal("50000")
    assert RegistroAuditoria.query.filter_by(entidad="obra", accion="aprobar_orden_cambio").count() == 1


def test_incidente_seguridad_se_registra(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Seguridad", cantidad=1, precio_unitario=1000)
    resp = client.post(f"/obras/{obra.id}/seguridad/nuevo", data={
        "fecha": "2026-03-01", "tipo": "incidente", "gravedad": "alta",
        "descripcion": "Caída de material desde andamio", "accion_tomada": "Se acordonó el área",
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert IncidenteSeguridad.query.filter_by(obra_id=obra.id).count() == 1


def test_asistencia_diaria_alimenta_nomina(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Asistencia", cantidad=1, precio_unitario=1000)
    trabajador = Trabajador(nombre="Pedro Asistente", oficio="albanil", tipo_pago="por_dia")
    db.session.add(trabajador)
    db.session.commit()

    lunes = date(2026, 3, 2)  # un lunes
    client.post(f"/obras/{obra.id}/asistencia?fecha={lunes.isoformat()}", data={
        "fecha": lunes.isoformat(), f"presente_{trabajador.id}": "on",
    })
    assert Asistencia.query.filter_by(trabajador_id=trabajador.id, presente=True).count() == 1

    resp = client.get(f"/trabajadores/nomina?semana={lunes.isoformat()}")
    assert resp.status_code == 200
    assert b"Pedro Asistente" in resp.data


def test_expediente_trabajador_y_ausencia(client, admin, app, tmp_path):
    app.instance_path = str(tmp_path)
    login(client, "admin@example.com", "Password123!")
    trabajador = Trabajador(nombre="Luis Expediente", oficio="pintor", tipo_pago="destajo")
    db.session.add(trabajador)
    db.session.commit()

    resp = client.post(f"/trabajadores/{trabajador.id}/documentos/nuevo", data={
        "nombre": "INE", "categoria": "identificacion",
        "archivo": (io.BytesIO(b"contenido"), "ine.pdf"),
    }, content_type="multipart/form-data", follow_redirects=False)
    assert resp.status_code == 302
    doc = DocumentoTrabajador.query.filter_by(trabajador_id=trabajador.id).first()
    assert doc.ruta_archivo.startswith("local:trabajadores/")

    resp = client.post(f"/trabajadores/{trabajador.id}/ausencias/nueva", data={
        "tipo": "vacaciones", "fecha_inicio": "2026-03-02", "fecha_fin": "2026-03-06", "motivo": "",
    }, follow_redirects=False)
    assert resp.status_code == 302
    assert AusenciaTrabajador.query.filter_by(trabajador_id=trabajador.id).count() == 1

    resp = client.get(f"/trabajadores/nomina?semana=2026-03-02")
    assert resp.status_code == 200
    assert b"vacaciones" in resp.data


def test_equipo_asignacion_y_liberacion(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Equipo", cantidad=1, precio_unitario=1000)

    client.post("/equipo/nuevo", data={
        "nombre": "Grúa torre", "tipo": "Grúa", "propio": "", "costo_renta_diario": "5000",
    })
    equipo = Equipo.query.filter_by(nombre="Grúa torre").first()
    assert equipo is not None

    client.post(f"/obras/{obra.id}/equipo/asignar", data={
        "equipo_id": str(equipo.id), "fecha_inicio": "2026-03-01", "notas": "",
    })
    asignacion = AsignacionEquipo.query.filter_by(obra_id=obra.id).first()
    assert asignacion.activa

    client.post(f"/obras/{obra.id}/equipo/{asignacion.id}/liberar")
    db.session.refresh(asignacion)
    assert not asignacion.activa


def test_subcontratista_contrato_y_avance(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Subcontrato", cantidad=1, precio_unitario=1000)

    client.post("/subcontratistas/nuevo", data={
        "nombre": "Instalaciones ABC", "especialidad": "Eléctricas", "contacto": "", "telefono": "",
    })
    sub = Subcontratista.query.filter_by(nombre="Instalaciones ABC").first()

    client.post(f"/obras/{obra.id}/subcontratos/nuevo", data={
        "subcontratista_id": str(sub.id), "concepto": "Instalación eléctrica completa",
        "monto": "80000", "fecha_inicio": "", "fecha_fin": "",
    })
    contrato = ContratoSubcontratista.query.filter_by(obra_id=obra.id).first()
    assert contrato is not None

    client.post(f"/obras/{obra.id}/subcontratos/{contrato.id}/avance", data={"avance_porcentaje": "100"})
    db.session.refresh(contrato)
    assert contrato.estado == "terminado"


def test_plantilla_de_cotizacion_se_carga_en_form(client, admin):
    login(client, "admin@example.com", "Password123!")
    plantilla = PlantillaCotizacion(nombre="Casa 100m2", tipo_obra="residencial")
    plantilla.items = [PlantillaItem(concepto="Cimentación estándar", unidad="lote", cantidad=1, precio_unitario=150000)]
    db.session.add(plantilla)
    db.session.commit()

    obra = _crear_obra_via_flujo(client, "Cliente Plantilla", cantidad=1, precio_unitario=1)
    levantamiento_id = obra.cotizacion.levantamiento_id

    resp = client.post(f"/cotizaciones/levantamiento/{levantamiento_id}/nueva", data={
        "titulo": "", "notas": "", "plantilla_id": str(plantilla.id), "accion": "cargar_plantilla",
        "items-0-concepto": "", "items-0-unidad": "pza", "items-0-cantidad": "1", "items-0-precio_unitario": "",
    })
    assert resp.status_code == 200
    assert b"Cimentaci\xc3\xb3n est\xc3\xa1ndar" in resp.data


def test_busqueda_avanzada_obras_y_clientes(client, admin):
    login(client, "admin@example.com", "Password123!")
    _crear_obra_via_flujo(client, "Constructora Búsqueda Única", cantidad=1, precio_unitario=1000)

    resp = client.get("/obras/?q=Búsqueda Única")
    assert resp.status_code == 200
    assert "Constructora Búsqueda Única".encode() in resp.data

    resp = client.get("/clientes/?q=Búsqueda Única")
    assert resp.status_code == 200
    assert "Constructora Búsqueda Única".encode() in resp.data


def test_firma_digital_se_guarda_al_aceptar_desde_portal(client, admin, app, tmp_path):
    app.instance_path = str(tmp_path)
    login(client, "admin@example.com", "Password123!")
    resp = client.post("/clientes/nuevo", data={
        "nombre": "Cliente Firma", "tipo": "persona_fisica",
        "email": "", "telefono": "", "rfc": "", "direccion": "", "notas": "",
    })
    from constructora.models import Cliente
    cliente = Cliente.query.filter_by(nombre="Cliente Firma").first()

    client.post("/levantamientos/nuevo", data={
        "cliente_id": str(cliente.id), "titulo": "Proyecto Firma",
        "tipo_obra": "residencial", "direccion": "", "indicaciones_cliente": "x",
    })
    from constructora.models import Levantamiento
    levantamiento = Levantamiento.query.filter_by(cliente_id=cliente.id).first()

    client.post(f"/cotizaciones/levantamiento/{levantamiento.id}/nueva", data={
        "titulo": "Cotización firma", "notas": "",
        "items-0-concepto": "Concepto", "items-0-unidad": "pza",
        "items-0-cantidad": "1", "items-0-precio_unitario": "1000",
    })
    cotizacion = Cotizacion.query.filter_by(levantamiento_id=levantamiento.id).first()
    client.post(f"/cotizaciones/{cotizacion.id}/enviar")
    client.get("/logout")

    acceso = ClienteAcceso(cliente_id=cliente.id, email="firma@example.com")
    acceso.set_password("PortalPass1!")
    db.session.add(acceso)
    db.session.commit()
    login(client, "firma@example.com", "PortalPass1!", portal=True)

    pixel_png_base64 = (
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42"
        "YAAAAASUVORK5CYII="
    )
    resp = client.post(f"/portal/cotizaciones/{cotizacion.id}/aceptar", data={"firma": pixel_png_base64}, follow_redirects=False)
    assert resp.status_code == 302
    db.session.refresh(cotizacion)
    assert cotizacion.firma_url is not None
    assert cotizacion.firma_url.startswith("local:firmas/")


def test_mensajeria_interna_y_portal(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Mensajes", cantidad=1, precio_unitario=1000)

    client.post(f"/obras/{obra.id}/mensajes/nuevo", data={"texto": "Buenas tardes, ¿cómo va el avance?"})
    assert MensajeObra.query.filter_by(obra_id=obra.id, autor_tipo="usuario").count() == 1

    client.get("/logout")
    acceso = ClienteAcceso(cliente_id=obra.cliente_id, email="mensajes@example.com")
    acceso.set_password("PortalPass1!")
    db.session.add(acceso)
    db.session.commit()
    login(client, "mensajes@example.com", "PortalPass1!", portal=True)

    client.post(f"/portal/obras/{obra.id}/mensajes/nuevo", data={"texto": "Va muy bien, gracias"})
    assert MensajeObra.query.filter_by(obra_id=obra.id, autor_tipo="cliente").count() == 1


def test_vencimiento_documentos_legales(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Vencimiento Doc", cantidad=1, precio_unitario=1000)
    db.session.add(Documento(
        obra_id=obra.id, nombre="Licencia de construcción", categoria="licencia",
        url_archivo="https://example.com/licencia.pdf", fecha_vencimiento=date.today() + timedelta(days=10),
        subido_por=admin.id,
    ))
    db.session.commit()

    n = avisar_documentos_por_vencer()
    assert n == 1
    doc = Documento.query.filter_by(obra_id=obra.id).first()
    assert doc.aviso_vencimiento_enviado is True


def test_dashboard_consolidado_y_exportaciones_csv(client, admin):
    login(client, "admin@example.com", "Password123!")
    _crear_obra_via_flujo(client, "Cliente Dashboard", cantidad=1, precio_unitario=1000)

    resp = client.get("/dashboard")
    assert resp.status_code == 200

    obra = Obra.query.first()
    resp = client.get(f"/obras/{obra.id}/gastos/exportar.csv")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"

    resp = client.get("/catalogo/exportar.csv")
    assert resp.status_code == 200


def test_reporte_cierre_con_curva_s(client, admin):
    login(client, "admin@example.com", "Password123!")
    obra = _crear_obra_via_flujo(client, "Cliente Curva S", cantidad=1, precio_unitario=100000)
    client.post(f"/obras/{obra.id}/avance/nuevo", data={
        "semana": "2026-03-02", "etapa": "Cimentación", "porcentaje": "20", "descripcion": "",
    })
    resp = client.get(f"/obras/{obra.id}/reporte-cierre")
    assert resp.status_code == 200


def test_pwa_manifest_y_service_worker_accesibles(client, admin):
    login(client, "admin@example.com", "Password123!")
    resp = client.get("/static/manifest.json")
    assert resp.status_code == 200
    resp = client.get("/static/sw.js")
    assert resp.status_code == 200


def test_auditoria_registra_aceptar_cotizacion_y_se_puede_ver(client, admin):
    login(client, "admin@example.com", "Password123!")
    _crear_obra_via_flujo(client, "Cliente Auditoria", cantidad=1, precio_unitario=1000)
    assert RegistroAuditoria.query.filter_by(accion="aceptar_cotizacion").count() == 1

    resp = client.get("/auditoria/")
    assert resp.status_code == 200
    assert b"aceptar_cotizacion" in resp.data
