from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from .extensions import db
from .decorators import roles_requeridos
from .forms import ClienteForm
from .models import Cliente

clientes_bp = Blueprint("clientes", __name__)


@clientes_bp.route("/")
@login_required
def lista():
    texto = request.args.get("q", "").strip()
    query = Cliente.query
    if texto:
        patron = f"%{texto}%"
        query = query.filter(db.or_(
            Cliente.nombre.ilike(patron), Cliente.email.ilike(patron),
            Cliente.telefono.ilike(patron), Cliente.rfc.ilike(patron),
        ))
    clientes = query.order_by(Cliente.creado_en.desc()).all()
    return render_template("clientes/lista.html", clientes=clientes, texto=texto)


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nuevo():
    form = ClienteForm()
    if form.validate_on_submit():
        cliente = Cliente(
            nombre=form.nombre.data.strip(),
            tipo=form.tipo.data,
            email=form.email.data,
            telefono=form.telefono.data,
            rfc=form.rfc.data,
            direccion=form.direccion.data,
            notas=form.notas.data,
        )
        db.session.add(cliente)
        db.session.commit()
        flash(f"Cliente '{cliente.nombre}' creado.", "success")
        return redirect(url_for("levantamientos.nuevo", cliente_id=cliente.id))
    return render_template("clientes/form.html", form=form, titulo="Nuevo cliente")


@clientes_bp.route("/<int:cliente_id>")
@login_required
def detalle(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("clientes/detalle.html", cliente=cliente)
