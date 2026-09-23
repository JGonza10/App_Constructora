"""Registro de auditoria para acciones criticas (montos, estados de obra y de
cotizacion) — no un log general de toda la app, solo lo que vale la pena poder
reconstruir despues: quien cambio que."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user

from .decorators import roles_requeridos
from .extensions import db
from .models import RegistroAuditoria

auditoria_bp = Blueprint("auditoria", __name__)


def registrar(accion, entidad, entidad_id, detalle=""):
    usuario_id = None
    usuario_nombre = "sistema"
    if current_user.is_authenticated:
        if current_user.tipo == "usuario":
            usuario_id, usuario_nombre = current_user.id, current_user.nombre
        elif current_user.tipo == "cliente":
            usuario_nombre = f"cliente: {current_user.cliente.nombre}"
    db.session.add(RegistroAuditoria(
        usuario_id=usuario_id, usuario_nombre=usuario_nombre,
        accion=accion, entidad=entidad, entidad_id=entidad_id, detalle=detalle,
    ))


@auditoria_bp.route("/")
@login_required
@roles_requeridos("admin")
def lista():
    registros = RegistroAuditoria.query.order_by(RegistroAuditoria.creado_en.desc()).limit(300).all()
    return render_template("auditoria/lista.html", registros=registros)
