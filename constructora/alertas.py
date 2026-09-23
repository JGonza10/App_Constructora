"""Alerta de sobrepresupuesto: se dispara al registrar un gasto o un pago de
mano de obra, comparando el gasto real de la obra contra su monto de contrato.

Los umbrales son dos niveles (90% y 100%) para no mandar una alerta por cada
gasto nuevo una vez que ya se cruzo un nivel — `Obra.nivel_alerta_presupuesto`
guarda el nivel mas alto ya notificado, y solo se vuelve a avisar si se cruza
un nivel superior."""
from .extensions import db
from .notificaciones import notificar

NIVELES = (90, 100)


def verificar_presupuesto(obra):
    if not obra.monto_contrato:
        return
    pct = obra.pct_gasto
    nivel_cruzado = max((n for n in NIVELES if pct >= n), default=0)

    if nivel_cruzado > (obra.nivel_alerta_presupuesto or 0):
        obra.nivel_alerta_presupuesto = nivel_cruzado
        db.session.commit()
        if nivel_cruzado >= 100:
            asunto = f"⚠️ Obra '{obra.nombre}' superó el presupuesto"
        else:
            asunto = f"⚠️ Obra '{obra.nombre}' cerca del límite de presupuesto"
        cuerpo = (
            f"Gasto real: ${obra.gasto_real:,.2f} de ${obra.monto_contrato:,.2f} "
            f"contratados ({pct}%).\nSaldo disponible: ${obra.saldo_presupuesto:,.2f}."
        )
        notificar(asunto, cuerpo)
    elif nivel_cruzado < (obra.nivel_alerta_presupuesto or 0):
        # El gasto bajo de nivel (p.ej. se corrigio un registro): permite que
        # se vuelva a avisar si el gasto vuelve a subir mas adelante.
        obra.nivel_alerta_presupuesto = nivel_cruzado
        db.session.commit()
