from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user

from .extensions import limiter
from .forms import PortalLoginForm
from .models import ClienteAcceso, Obra

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
    return render_template("portal/obras.html", obras=obras)


@portal_bp.route("/obras/<int:obra_id>")
@login_required
def obra_detalle(obra_id):
    if current_user.tipo != "cliente":
        abort(403)
    obra = _obra_del_cliente_o_404(obra_id)
    documentos_visibles = [d for d in obra.documentos if d.visible_cliente]
    return render_template("portal/obra_detalle.html", obra=obra, documentos=documentos_visibles)
