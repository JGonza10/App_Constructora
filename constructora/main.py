from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from .models import Obra, Levantamiento, Cotizacion

main_bp = Blueprint("main", __name__)


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
    if current_user.puede_gestionar_obras():
        kpis = {
            "monto_contratado": sum((o.monto_contrato for o in obras_activas), start=0),
            "gasto_real": sum((o.gasto_real for o in obras_activas), start=0),
            "obras_activas": len(obras_activas),
        }

    return render_template(
        "dashboard.html",
        obras_activas=obras_activas,
        levantamientos_abiertos=levantamientos_abiertos,
        cotizaciones_pendientes=cotizaciones_pendientes,
        kpis=kpis,
    )
