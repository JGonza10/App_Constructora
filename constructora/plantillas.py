from flask import Blueprint, render_template, redirect, url_for, flash, request

from flask_login import login_required

from .decorators import roles_requeridos
from .extensions import db
from .forms import PlantillaCotizacionForm
from .models import PlantillaCotizacion, PlantillaItem

plantillas_bp = Blueprint("plantillas", __name__)


@plantillas_bp.route("/")
@login_required
def lista():
    plantillas = PlantillaCotizacion.query.order_by(PlantillaCotizacion.nombre).all()
    return render_template("plantillas/lista.html", plantillas=plantillas)


@plantillas_bp.route("/nueva", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nueva():
    form = PlantillaCotizacionForm()

    if request.method == "POST" and request.form.get("accion") == "agregar_linea":
        form.items.append_entry()
        return render_template("plantillas/form.html", form=form)

    if form.validate_on_submit():
        items_validos = [
            it for it in form.items.entries
            if it.form.concepto.data and it.form.precio_unitario.data
        ]
        if not items_validos:
            flash("Agrega al menos un concepto con precio.", "warning")
            return render_template("plantillas/form.html", form=form)

        plantilla = PlantillaCotizacion(nombre=form.nombre.data.strip(), tipo_obra=form.tipo_obra.data)
        for it in items_validos:
            plantilla.items.append(PlantillaItem(
                concepto=it.form.concepto.data, unidad=it.form.unidad.data,
                cantidad=it.form.cantidad.data, precio_unitario=it.form.precio_unitario.data,
            ))
        db.session.add(plantilla)
        db.session.commit()
        flash(f"Plantilla '{plantilla.nombre}' guardada.", "success")
        return redirect(url_for("plantillas.lista"))

    return render_template("plantillas/form.html", form=form)


@plantillas_bp.route("/<int:plantilla_id>/eliminar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def eliminar(plantilla_id):
    plantilla = PlantillaCotizacion.query.get_or_404(plantilla_id)
    db.session.delete(plantilla)
    db.session.commit()
    flash("Plantilla eliminada.", "success")
    return redirect(url_for("plantillas.lista"))
