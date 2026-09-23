from collections import OrderedDict

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from .models import Obra, Levantamiento, Cotizacion

main_bp = Blueprint("main", __name__)


def _flujo_caja_consolidado(obras_activas):
    """Suma el flujo de caja de todas las obras activas por mes — la version
    de obras._flujo_caja() pero para el negocio completo, no una sola obra."""
    meses = OrderedDict()

    def _sumar(fecha, campo, monto):
        clave = f"{fecha.year}-{fecha.month:02d}"
        meses.setdefault(clave, {"ingresos": 0, "egresos": 0})
        meses[clave][campo] += float(monto)

    for obra in obras_activas:
        for g in obra.gastos:
            _sumar(g.fecha, "egresos", g.monto)
        for p in obra.pagos_mano_obra:
            _sumar(p.fecha, "egresos", p.monto)
        for p in obra.pagos_cliente:
            if p.fecha_recibido:
                _sumar(p.fecha_recibido, "ingresos", p.monto)

    claves = sorted(meses.keys())
    return {
        "etiquetas": claves,
        "ingresos": [round(meses[c]["ingresos"], 2) for c in claves],
        "egresos": [round(meses[c]["egresos"], 2) for c in claves],
    }


@main_bp.route("/")
def inicio():
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.tipo != "usuario":
        return redirect(url_for("portal.obras"))

    obras_activas = Obra.query.filter_by(estado="activa").all()
    levantamientos_abiertos = Levantamiento.query.filter(
        Levantamiento.estado.in_(["nuevo", "en_cotizacion"])
    ).order_by(Levantamiento.creado_en.desc()).limit(10).all()
    cotizaciones_pendientes = Cotizacion.query.filter_by(estado="enviada").all()

    kpis = None
    flujo_caja_consolidado = None
    if current_user.puede_gestionar_obras():
        kpis = {
            "monto_contratado": sum((o.monto_contrato for o in obras_activas), start=0),
            "gasto_real": sum((o.gasto_real for o in obras_activas), start=0),
            "obras_activas": len(obras_activas),
        }
        flujo_caja_consolidado = _flujo_caja_consolidado(obras_activas)

    return render_template(
        "dashboard.html",
        obras_activas=obras_activas,
        levantamientos_abiertos=levantamientos_abiertos,
        cotizaciones_pendientes=cotizaciones_pendientes,
        kpis=kpis,
        flujo_caja_consolidado=flujo_caja_consolidado,
    )
