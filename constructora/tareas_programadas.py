"""Job diario: pasa a 'vencido' los pagos del cliente que ya cumplieron su
fecha programada y siguen pendientes, y avisa por los canales de notificacion.
Se dispara solo via APScheduler (ver __init__.create_app) o a mano desde
`flask --app wsgi vencer-pagos` — nunca desde una peticion HTTP normal."""
from datetime import date, timedelta

from .extensions import db
from .models import PagoCliente, Documento
from .notificaciones import notificar

DIAS_AVISO_VENCIMIENTO_DOCUMENTO = 30


def marcar_pagos_vencidos():
    hoy = date.today()
    pagos = PagoCliente.query.filter(
        PagoCliente.estado == "pendiente",
        PagoCliente.fecha_programada < hoy,
    ).all()

    for pago in pagos:
        pago.estado = "vencido"

    if pagos:
        db.session.commit()
        detalle = "\n".join(
            f"- {p.obra.nombre}: {p.concepto} — ${p.monto:,.2f} "
            f"(programado {p.fecha_programada.strftime('%d/%m/%Y')})"
            for p in pagos
        )
        notificar(
            f"⏰ {len(pagos)} pago(s) de cliente vencido(s)",
            f"Se marcaron como vencidos los siguientes pagos programados:\n{detalle}",
        )

    return len(pagos)


def avisar_documentos_por_vencer():
    """Documentos legales (licencias, polizas, permisos) con fecha_vencimiento
    dentro de los proximos DIAS_AVISO_VENCIMIENTO_DOCUMENTO dias. Se avisa una
    sola vez por documento (aviso_vencimiento_enviado), no cada dia."""
    limite = date.today() + timedelta(days=DIAS_AVISO_VENCIMIENTO_DOCUMENTO)
    documentos = Documento.query.filter(
        Documento.fecha_vencimiento.isnot(None),
        Documento.fecha_vencimiento <= limite,
        Documento.aviso_vencimiento_enviado.is_(False),
    ).all()

    for doc in documentos:
        doc.aviso_vencimiento_enviado = True

    if documentos:
        db.session.commit()
        detalle = "\n".join(
            f"- {d.obra.nombre}: {d.nombre} — vence {d.fecha_vencimiento.strftime('%d/%m/%Y')}"
            for d in documentos
        )
        notificar(
            f"📄 {len(documentos)} documento(s) por vencer",
            f"Vencen en los próximos {DIAS_AVISO_VENCIMIENTO_DOCUMENTO} días:\n{detalle}",
        )

    return len(documentos)
