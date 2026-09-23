from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from .decorators import roles_requeridos
from .extensions import db
from .forms import SubcontratistaForm
from .models import Subcontratista

subcontratistas_bp = Blueprint("subcontratistas", __name__)


@subcontratistas_bp.route("/")
@login_required
def lista():
    subcontratistas = Subcontratista.query.filter_by(activo=True).order_by(Subcontratista.nombre).all()
    return render_template("subcontratistas/lista.html", subcontratistas=subcontratistas)


@subcontratistas_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nuevo():
    form = SubcontratistaForm()
    if form.validate_on_submit():
        db.session.add(Subcontratista(
            nombre=form.nombre.data.strip(), especialidad=form.especialidad.data,
            contacto=form.contacto.data, telefono=form.telefono.data,
        ))
        db.session.commit()
        flash(f"Subcontratista '{form.nombre.data}' registrado.", "success")
        return redirect(url_for("subcontratistas.lista"))
    return render_template("subcontratistas/form.html", form=form)
