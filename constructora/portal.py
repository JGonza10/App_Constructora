from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_user, logout_user, login_required, current_user

from .cotizaciones import crear_obra_desde_cotizacion, rechazar_cotizacion
from .decorators import solo_cliente_portal
from .extensions import db, limiter
from .forms import PortalLoginForm, PortalRechazoCotizacionForm, MensajeObraForm
from .models import ClienteAcceso, Cotizacion, Levantamiento, Obra, MensajeObra

portal_bp = Blueprint("portal", __name__)


@portal_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("8 per 15 minutes", methods=["POST"])
def login():
    if current_user.is_authenticated and current_user.tipo == "cliente":
        return redirect(url_for("portal.obras"))

    form = PortalLoginForm()
    if form.validate_on_submit():
        acceso = ClienteAcceso.query.filter_by(email=form.email.data.lower().strip(), activo=True).first()
        if acceso and acceso.check_password(form.password.data):
            login_user(acceso)
            return redirect(url_for("portal.obras"))
        flash("Credenciales inválidas.", "danger")
    return render_template("portal/login.html", form=form)


@portal_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("portal.login"))


def _obra_del_cliente_o_404(obra_id):
    obra = Obra.query.filter_by(id=obra_id, cliente_id=current_user.cliente_id).first()
    if not obra:
        abort(404)
    return obra


@portal_bp.route("/obras")
@login_required
def obras():
    if current_user.tipo != "cliente":
        abort(403)
    obras = Obra.query.filter_by(cliente_id=current_user.cliente_id).all()
    return render_template(
        "portal/obras.html", obras=obras,
        cotizaciones_pendientes=len(_cotizaciones_pendientes_del_cliente()),
    )


@portal_bp.route("/obras/<int:obra_id>")
@login_required
def obra_detalle(obra_id):
    if current_user.tipo != "cliente":
        abort(403)
    obra = _obra_del_cliente_o_404(obra_id)
    documentos_visibles = [d for d in obra.documentos if d.visible_cliente]
    return render_template("portal/obra_detalle.html", obra=obra, documentos=documentos_visibles)


def _cotizaciones_pendientes_del_cliente():
    return (
        Cotizacion.query.join(Levantamiento)
        .filter(Levantamiento.cliente_id == current_user.cliente_id, Cotizacion.estado == "enviada")
        .order_by(Cotizacion.creado_en.desc())
        .all()
    )


def _cotizacion_del_cliente_o_404(cotizacion_id):
    cotizacion = (
        Cotizacion.query.join(Levantamiento)
        .filter(Cotizacion.id == cotizacion_id, Levantamiento.cliente_id == current_user.cliente_id)
        .first()
    )
    if not cotizacion:
        abort(404)
    return cotizacion


@portal_bp.route("/cotizaciones")
@login_required
@solo_cliente_portal
def cotizaciones():
    return render_template("portal/cotizaciones.html", cotizaciones=_cotizaciones_pendientes_del_cliente())


@portal_bp.route("/cotizaciones/<int:cotizacion_id>")
@login_required
@solo_cliente_portal
def cotizacion_detalle(cotizacion_id):
    cotizacion = _cotizacion_del_cliente_o_404(cotizacion_id)
    return render_template(
        "portal/cotizacion_detalle.html",
        cotizacion=cotizacion, form_rechazo=PortalRechazoCotizacionForm(),
    )


@portal_bp.route("/cotizaciones/<int:cotizacion_id>/aceptar", methods=["POST"])
@login_required
@solo_cliente_portal
def aceptar_cotizacion(cotizacion_id):
    cotizacion = _cotizacion_del_cliente_o_404(cotizacion_id)
    if cotizacion.estado != "enviada":
        flash("Esta cotización ya no está disponible para aceptar.", "danger")
        return redirect(url_for("portal.cotizaciones"))

    obra = crear_obra_desde_cotizacion(cotizacion, firma_data_url=request.form.get("firma"))
    flash(f"¡Cotización aceptada! Ya puedes seguir el avance de '{obra.nombre}' desde tu portal.", "success")
    return redirect(url_for("portal.obra_detalle", obra_id=obra.id))


@portal_bp.route("/cotizaciones/<int:cotizacion_id>/rechazar", methods=["POST"])
@login_required
@solo_cliente_portal
def rechazar_cotizacion_portal(cotizacion_id):
    cotizacion = _cotizacion_del_cliente_o_404(cotizacion_id)
    form = PortalRechazoCotizacionForm()
    if cotizacion.estado != "enviada" or not form.validate_on_submit():
        flash("No se pudo registrar el rechazo.", "danger")
        return redirect(url_for("portal.cotizacion_detalle", cotizacion_id=cotizacion.id))

    rechazar_cotizacion(cotizacion, form.motivo_rechazo.data)
    flash("Cotización rechazada. El equipo de la constructora preparará una nueva versión.", "warning")
    return redirect(url_for("portal.cotizaciones"))


@portal_bp.route("/obras/<int:obra_id>/mensajes/nuevo", methods=["POST"])
@login_required
@solo_cliente_portal
def nuevo_mensaje(obra_id):
    obra = _obra_del_cliente_o_404(obra_id)
    form = MensajeObraForm()
    if form.validate_on_submit():
        db.session.add(MensajeObra(
            obra_id=obra.id, autor_tipo="cliente", autor_nombre=current_user.cliente.nombre, texto=form.texto.data,
        ))
        db.session.commit()
    return redirect(url_for("portal.obra_detalle", obra_id=obra_id))
