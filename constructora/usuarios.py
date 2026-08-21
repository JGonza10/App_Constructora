from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from .extensions import db
from .decorators import roles_requeridos
from .forms import UsuarioForm
from .models import Usuario

usuarios_bp = Blueprint("usuarios", __name__)


@usuarios_bp.route("/")
@login_required
@roles_requeridos("admin", "supervisor")
def lista():
    usuarios = Usuario.query.order_by(Usuario.creado_en.desc()).all()
    return render_template("usuarios/lista.html", usuarios=usuarios)


@usuarios_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin")
def nuevo():
    form = UsuarioForm()
    if form.validate_on_submit():
        if Usuario.query.filter_by(email=form.email.data.lower().strip()).first():
            flash("Ya existe un usuario con ese email.", "danger")
        else:
            usuario = Usuario(nombre=form.nombre.data.strip(), email=form.email.data.lower().strip(), rol=form.rol.data)
            usuario.set_password(form.password.data)
            db.session.add(usuario)
            db.session.commit()
            flash(f"Usuario '{usuario.nombre}' creado.", "success")
            return redirect(url_for("usuarios.lista"))
    return render_template("usuarios/form.html", form=form)


@usuarios_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@login_required
@roles_requeridos("admin")
def toggle_estado(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    usuario.activo = not usuario.activo
    db.session.commit()
    flash(f"Usuario {'activado' if usuario.activo else 'desactivado'}.", "success")
    return redirect(url_for("usuarios.lista"))
