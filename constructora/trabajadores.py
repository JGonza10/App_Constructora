from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from .extensions import db
from .forms import TrabajadorForm
from .models import Trabajador

trabajadores_bp = Blueprint("trabajadores", __name__)


@trabajadores_bp.route("/")
@login_required
def lista():
    trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre).all()
    return render_template("trabajadores/lista.html", trabajadores=trabajadores)


@trabajadores_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = TrabajadorForm()
    obra_id = request.args.get("obra_id", type=int)
    if form.validate_on_submit():
        db.session.add(Trabajador(
            nombre=form.nombre.data, oficio=form.oficio.data,
            telefono=form.telefono.data, tipo_pago=form.tipo_pago.data,
        ))
        db.session.commit()
        flash(f"Trabajador '{form.nombre.data}' registrado.", "success")
        if obra_id:
            return redirect(url_for("obras.nuevo_pago_mano_obra", obra_id=obra_id))
        return redirect(url_for("trabajadores.lista"))
    return render_template("trabajadores/form.html", form=form, obra_id=obra_id)
