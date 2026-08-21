from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from .extensions import db
from .forms import LevantamientoForm
from .models import Levantamiento, Cliente

levantamientos_bp = Blueprint("levantamientos", __name__)


def _form_con_clientes(form):
    form.cliente_id.choices = [(c.id, c.nombre) for c in Cliente.query.order_by(Cliente.nombre).all()]
    return form


@levantamientos_bp.route("/")
@login_required
def lista():
    levantamientos = Levantamiento.query.order_by(Levantamiento.creado_en.desc()).all()
    return render_template("levantamientos/lista.html", levantamientos=levantamientos)


@levantamientos_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = _form_con_clientes(LevantamientoForm())
    cliente_preseleccionado = request.args.get("cliente_id", type=int)
    if request.method == "GET" and cliente_preseleccionado:
        form.cliente_id.data = cliente_preseleccionado

    if form.validate_on_submit():
        levantamiento = Levantamiento(
            cliente_id=form.cliente_id.data,
            titulo=form.titulo.data.strip(),
            tipo_obra=form.tipo_obra.data,
            direccion=form.direccion.data,
            indicaciones_cliente=form.indicaciones_cliente.data,
            fecha_visita=form.fecha_visita.data,
            creado_por=current_user.id,
        )
        db.session.add(levantamiento)
        db.session.commit()
        flash("Levantamiento guardado con las indicaciones del cliente.", "success")
        return redirect(url_for("levantamientos.siguiente_paso", levantamiento_id=levantamiento.id))

    return render_template("levantamientos/form.html", form=form, titulo="Nuevo levantamiento")


@levantamientos_bp.route("/<int:levantamiento_id>/siguiente-paso")
@login_required
def siguiente_paso(levantamiento_id):
    """Pantalla puente del flujo guiado: acaba de capturarse el levantamiento,
    el siguiente paso natural es armar la cotizacion."""
    levantamiento = Levantamiento.query.get_or_404(levantamiento_id)
    return render_template("levantamientos/siguiente_paso.html", levantamiento=levantamiento)


@levantamientos_bp.route("/<int:levantamiento_id>")
@login_required
def detalle(levantamiento_id):
    levantamiento = Levantamiento.query.get_or_404(levantamiento_id)
    return render_template("levantamientos/detalle.html", levantamiento=levantamiento)
