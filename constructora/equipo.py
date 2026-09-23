from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from .decorators import roles_requeridos
from .extensions import db
from .forms import EquipoForm
from .models import Equipo

equipo_bp = Blueprint("equipo", __name__)


@equipo_bp.route("/")
@login_required
def lista():
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()
    return render_template("equipo/lista.html", equipos=equipos, hoy=date.today())


@equipo_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nuevo():
    form = EquipoForm()
    if form.validate_on_submit():
        db.session.add(Equipo(
            nombre=form.nombre.data.strip(), tipo=form.tipo.data,
            propio=form.propio.data, costo_renta_diario=form.costo_renta_diario.data,
        ))
        db.session.commit()
        flash(f"Equipo '{form.nombre.data}' registrado.", "success")
        return redirect(url_for("equipo.lista"))
    return render_template("equipo/form.html", form=form)
