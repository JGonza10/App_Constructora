import csv
import io

from flask import Blueprint, render_template, redirect, url_for, flash, Response
from flask_login import login_required

from .extensions import db
from .decorators import roles_requeridos
from .forms import ConceptoCatalogoForm
from .models import ConceptoCatalogo

catalogo_bp = Blueprint("catalogo", __name__)


@catalogo_bp.route("/")
@login_required
def lista():
    conceptos = ConceptoCatalogo.query.filter_by(activo=True).order_by(ConceptoCatalogo.concepto).all()
    return render_template("catalogo/lista.html", conceptos=conceptos)


@catalogo_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nuevo():
    form = ConceptoCatalogoForm()
    if form.validate_on_submit():
        db.session.add(ConceptoCatalogo(
            concepto=form.concepto.data.strip(), unidad=form.unidad.data.strip(),
            precio_unitario=form.precio_unitario.data, categoria=form.categoria.data,
        ))
        db.session.commit()
        flash("Concepto agregado al catálogo.", "success")
        return redirect(url_for("catalogo.lista"))
    return render_template("catalogo/form.html", form=form)


@catalogo_bp.route("/exportar.csv")
@login_required
def exportar_csv():
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["Concepto", "Categoría", "Unidad", "Precio unitario"])
    for c in ConceptoCatalogo.query.filter_by(activo=True).order_by(ConceptoCatalogo.concepto).all():
        escritor.writerow([c.concepto, c.categoria or "", c.unidad, f"{c.precio_unitario:.2f}"])
    return Response(
        salida.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=catalogo_conceptos.csv"},
    )


@catalogo_bp.route("/<int:concepto_id>/eliminar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def eliminar(concepto_id):
    concepto = ConceptoCatalogo.query.get_or_404(concepto_id)
    concepto.activo = False
    db.session.commit()
    flash("Concepto quitado del catálogo.", "success")
    return redirect(url_for("catalogo.lista"))
