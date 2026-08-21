"""
Recrea el esquema desde cero y carga un escenario de ejemplo completo,
recorriendo el flujo real: cliente -> levantamiento -> cotizacion (aceptada)
-> obra -> gastos / mano de obra / avance / tareas / bitacora / documentos / pagos.

ADVERTENCIA: borra todas las tablas y las vuelve a crear. Uso previsto:
desarrollo local y la carga inicial de datos de demo. No lo corras contra
una base de datos con información real de clientes.

Uso:
    python seed.py
"""
from datetime import date, datetime

from dotenv import load_dotenv
load_dotenv()

from constructora import create_app
from constructora.extensions import db
from constructora.models import (
    Usuario, Cliente, ClienteAcceso, Levantamiento, Cotizacion, CotizacionItem,
    Obra, Proveedor, Trabajador, PagoManoObra, Gasto, AvanceObra, Tarea,
    BitacoraObra, Documento, PagoCliente,
)

app = create_app()

with app.app_context():
    print("Recreando esquema...")
    db.drop_all()
    db.create_all()

    # ── Usuarios internos ──────────────────────────────────────────
    admin = Usuario(nombre="Ana Ramírez", email="ana.ramirez@constructora.com", rol="admin")
    admin.set_password("Direccion#2026")
    supervisor = Usuario(nombre="Jorge Villaseñor", email="jorge.villasenor@constructora.com", rol="supervisor")
    supervisor.set_password("Supervisa#2026")
    empleado = Usuario(nombre="Paola Reyes", email="paola.reyes@constructora.com", rol="empleado")
    empleado.set_password("Campo#2026")
    db.session.add_all([admin, supervisor, empleado])
    db.session.commit()

    # ── Clientes ────────────────────────────────────────────────────
    cliente1 = Cliente(nombre="Familia Delgado Ríos", email="delgado.rios@example.com",
                        telefono="5511122233", rfc="DERI850312AB4", tipo="persona_fisica")
    cliente2 = Cliente(nombre="Grupo Constructor Altavista SA de CV", email="contacto@altavista.mx",
                        telefono="5544455566", rfc="GCA150822CD7", tipo="empresa")
    db.session.add_all([cliente1, cliente2])
    db.session.commit()

    acceso1 = ClienteAcceso(cliente_id=cliente1.id, email="delgado.rios@example.com")
    acceso1.set_password("Cliente#2026")
    acceso2 = ClienteAcceso(cliente_id=cliente2.id, email="contacto@altavista.mx")
    acceso2.set_password("Altavista#2026")
    db.session.add_all([acceso1, acceso2])
    db.session.commit()

    # ── Levantamientos (lo que pidio cada cliente) ─────────────────
    lev1 = Levantamiento(
        cliente_id=cliente1.id, titulo="Residencia Delgado Ríos", tipo_obra="residencial",
        direccion="Calle Pinos 145, Col. Jardines", fecha_visita=date(2026, 2, 1),
        indicaciones_cliente=(
            "Construcción de casa habitación de 2 niveles: cimentación, estructura, "
            "instalaciones y acabados. Prioridad en cimentación resistente por terreno arcilloso."
        ),
        estado="cotizado", creado_por=supervisor.id,
    )
    lev2 = Levantamiento(
        cliente_id=cliente2.id, titulo="Plaza Comercial Altavista", tipo_obra="comercial",
        direccion="Av. Altavista 900", fecha_visita=date(2026, 2, 20),
        indicaciones_cliente=(
            "Nave comercial de dos niveles con 12 locales. Piden instalaciones eléctricas "
            "e hidráulicas completas antes de fin de año fiscal."
        ),
        estado="cotizado", creado_por=supervisor.id,
    )
    db.session.add_all([lev1, lev2])
    db.session.commit()

    # ── Cotizaciones aceptadas -> nacen las obras ──────────────────
    cot1 = Cotizacion(levantamiento_id=lev1.id, version=1, titulo="Cimentación y estructura",
                       estado="aceptada", creado_por=empleado.id, respondida_en=datetime(2026, 2, 8))
    cot1.items = [
        CotizacionItem(concepto="Excavación y plantilla", unidad="m3", cantidad=180, precio_unitario=850),
        CotizacionItem(concepto="Colado de zapatas y trabes de liga", unidad="m3", cantidad=120, precio_unitario=1980),
        CotizacionItem(concepto="Estructura y castillos", unidad="pza", cantidad=48, precio_unitario=4200),
    ]
    cot2 = Cotizacion(levantamiento_id=lev2.id, version=1, titulo="Instalaciones eléctricas e hidráulicas",
                       estado="aceptada", creado_por=empleado.id, respondida_en=datetime(2026, 2, 25))
    cot2.items = [
        CotizacionItem(concepto="Instalación eléctrica completa", unidad="lote", cantidad=1, precio_unitario=3200000),
        CotizacionItem(concepto="Instalación hidráulica completa", unidad="lote", cantidad=1, precio_unitario=1600000),
        CotizacionItem(concepto="Renta de grúa torre (3 meses)", unidad="mes", cantidad=3, precio_unitario=65000),
    ]
    db.session.add_all([cot1, cot2])
    db.session.commit()

    obra1 = Obra(
        cotizacion_id=cot1.id, cliente_id=cliente1.id, nombre=lev1.titulo, tipo="residencial",
        monto_contrato=cot1.total, responsable_id=supervisor.id,
        fecha_inicio=date(2026, 2, 10), fecha_fin_estimada=date(2026, 11, 30),
        estado="activa", avance_porcentaje=35, direccion=lev1.direccion, descripcion=lev1.indicaciones_cliente,
    )
    obra2 = Obra(
        cotizacion_id=cot2.id, cliente_id=cliente2.id, nombre=lev2.titulo, tipo="comercial",
        monto_contrato=cot2.total, responsable_id=supervisor.id,
        fecha_inicio=date(2026, 3, 1), fecha_fin_estimada=date(2027, 5, 31),
        estado="activa", avance_porcentaje=12, direccion=lev2.direccion, descripcion=lev2.indicaciones_cliente,
    )
    db.session.add_all([obra1, obra2])
    db.session.commit()

    # ── Proveedores ─────────────────────────────────────────────────
    prov1 = Proveedor(nombre="CEMEX México", contacto="Ventas CDMX", telefono="8008026326", categoria="materiales")
    prov2 = Proveedor(nombre="Aceros del Bajío", contacto="Carlos Méndez", telefono="5544332211", categoria="materiales")
    db.session.add_all([prov1, prov2])
    db.session.commit()

    # ── Trabajadores ────────────────────────────────────────────────
    albanil = Trabajador(nombre="Ramiro Cortés", oficio="albanil", telefono="5533221100", tipo_pago="semana")
    pintor = Trabajador(nombre="Beto Salgado", oficio="pintor", telefono="5599887766", tipo_pago="destajo")
    electricista = Trabajador(nombre="Iván Gómez", oficio="electricista", telefono="5511998877", tipo_pago="por_dia")
    db.session.add_all([albanil, pintor, electricista])
    db.session.commit()

    # ── Gastos de materiales ────────────────────────────────────────
    db.session.add_all([
        Gasto(obra_id=obra1.id, categoria="materiales", concepto="Concreto premezclado", cantidad=40, unidad="m3",
              monto=58000, fecha=date(2026, 2, 20), proveedor_id=prov1.id, registrado_por=empleado.id),
        Gasto(obra_id=obra2.id, categoria="materiales", concepto="Acero de refuerzo", cantidad=8, unidad="ton",
              monto=142000, fecha=date(2026, 3, 20), proveedor_id=prov2.id, registrado_por=empleado.id),
        Gasto(obra_id=obra2.id, categoria="equipo", concepto="Renta de grúa torre - marzo", monto=65000,
              fecha=date(2026, 3, 25), registrado_por=empleado.id),
    ])

    # ── Pagos de mano de obra ───────────────────────────────────────
    db.session.add_all([
        PagoManoObra(obra_id=obra1.id, trabajador_id=albanil.id, concepto="Semana 1-8 feb, cimentación",
                     dias_o_unidades=6, monto=9000, fecha=date(2026, 2, 8), registrado_por=empleado.id),
        PagoManoObra(obra_id=obra1.id, trabajador_id=pintor.id, concepto="Pintura fachada exterior (destajo)",
                     dias_o_unidades=1, monto=18000, fecha=date(2026, 3, 5), registrado_por=empleado.id),
        PagoManoObra(obra_id=obra2.id, trabajador_id=electricista.id, concepto="Instalación eléctrica planta baja",
                     dias_o_unidades=10, monto=15000, fecha=date(2026, 3, 22), registrado_por=empleado.id),
    ])

    # ── Avance semanal ──────────────────────────────────────────────
    db.session.add_all([
        AvanceObra(obra_id=obra1.id, semana=date(2026, 2, 16), etapa="Cimentación", porcentaje=20,
                   descripcion="Excavación y plantilla terminadas", reportado_por=empleado.id),
        AvanceObra(obra_id=obra1.id, semana=date(2026, 3, 2), etapa="Cimentación", porcentaje=35,
                   descripcion="Colado de zapatas y trabes de liga", reportado_por=empleado.id),
        AvanceObra(obra_id=obra2.id, semana=date(2026, 3, 9), etapa="Preliminares", porcentaje=12,
                   descripcion="Trazo, nivelación y cimbra inicial", reportado_por=empleado.id),
    ])

    # ── Tareas ──────────────────────────────────────────────────────
    db.session.add_all([
        Tarea(obra_id=obra1.id, titulo="Solicitar inspección municipal de cimentación",
              responsable_id=empleado.id, fecha_fin=date(2026, 3, 10), prioridad="alta", creado_por=supervisor.id),
        Tarea(obra_id=obra2.id, titulo="Cotizar segunda entrega de acero", estado="en_curso",
              responsable_id=empleado.id, fecha_fin=date(2026, 3, 28), prioridad="media", creado_por=supervisor.id),
    ])

    # ── Bitácora ────────────────────────────────────────────────────
    db.session.add_all([
        BitacoraObra(obra_id=obra1.id, fecha=date(2026, 3, 2), clima="soleado", personal_en_obra=8,
                     actividades="Colado de zapatas, cuadrilla completa", registrado_por=empleado.id),
        BitacoraObra(obra_id=obra2.id, fecha=date(2026, 3, 9), clima="nublado", personal_en_obra=12,
                     actividades="Trazo y nivelación de plataforma",
                     incidencias="Retraso de 2h por lluvia en la mañana", registrado_por=empleado.id),
    ])

    # ── Documentos ──────────────────────────────────────────────────
    db.session.add_all([
        Documento(obra_id=obra1.id, nombre="Planos arquitectónicos v1", categoria="plano",
                  url_archivo="/docs/obra1/planos_v1.pdf", visible_cliente=True, subido_por=admin.id),
        Documento(obra_id=obra1.id, nombre="Contrato de obra firmado", categoria="contrato",
                  url_archivo="/docs/obra1/contrato.pdf", visible_cliente=False, subido_por=admin.id),
        Documento(obra_id=obra2.id, nombre="Planos estructurales", categoria="plano",
                  url_archivo="/docs/obra2/estructurales.pdf", visible_cliente=True, subido_por=admin.id),
    ])

    # ── Pagos del cliente ───────────────────────────────────────────
    db.session.add_all([
        PagoCliente(obra_id=obra1.id, concepto="Anticipo 30%", monto=float(obra1.monto_contrato) * 0.3,
                    fecha_programada=date(2026, 2, 10), fecha_recibido=date(2026, 2, 10), estado="recibido"),
        PagoCliente(obra_id=obra1.id, concepto="Avance 40%", monto=float(obra1.monto_contrato) * 0.4,
                    fecha_programada=date(2026, 6, 30), estado="pendiente"),
        PagoCliente(obra_id=obra2.id, concepto="Anticipo 25%", monto=float(obra2.monto_contrato) * 0.25,
                    fecha_programada=date(2026, 3, 1), fecha_recibido=date(2026, 3, 3), estado="recibido"),
        PagoCliente(obra_id=obra2.id, concepto="Primera estimación", monto=float(obra2.monto_contrato) * 0.2,
                    fecha_programada=date(2026, 6, 15), estado="vencido"),
    ])

    db.session.commit()

    print("Listo. Escenario de ejemplo cargado:")
    print("  admin:      ana.ramirez@constructora.com      / Direccion#2026")
    print("  supervisor: jorge.villasenor@constructora.com  / Supervisa#2026")
    print("  empleado:   paola.reyes@constructora.com       / Campo#2026")
    print("  portal:     delgado.rios@example.com           / Cliente#2026")
    print("  portal:     contacto@altavista.mx              / Altavista#2026")
