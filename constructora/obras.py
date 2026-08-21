from datetime import date

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from .extensions import db
from .decorators import roles_requeridos
from .forms import (
    GastoForm, PagoManoObraForm, AvanceForm, TareaForm, BitacoraForm,
    DocumentoForm, PagoClienteForm,
)
from .models import (
    Obra, Gasto, PagoManoObra, Trabajador, AvanceObra, Tarea, BitacoraObra,
    Documento, PagoCliente, Proveedor, Usuario,
)

obras_bp = Blueprint("obras", __name__)


@obras_bp.route("/")
@login_required
def lista():
    filtro = request.args.get("estado", "todas")
    query = Obra.query
    if filtro != "todas":
        query = query.filter_by(estado=filtro)
    obras = query.order_by(Obra.creado_en.desc()).all()
    return render_template("obras/lista.html", obras=obras, filtro=filtro)


@obras_bp.route("/<int:obra_id>")
@login_required
def detalle(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    return render_template("obras/detalle.html", obra=obra)


@obras_bp.route("/<int:obra_id>/siguiente-paso")
@login_required
def siguiente_paso(obra_id):
    """Pantalla que aparece justo despues de que una cotizacion se acepta y
    nace la obra: ofrece los primeros registros tipicos en vez de dejar al
    usuario adivinar por donde empezar."""
    obra = Obra.query.get_or_404(obra_id)
    return render_template("obras/siguiente_paso_inicial.html", obra=obra)


def _siguiente_registro(obra, tipo):
    return redirect(url_for("obras.siguiente_registro", obra_id=obra.id, tipo=tipo))


@obras_bp.route("/<int:obra_id>/siguiente-registro/<tipo>")
@login_required
def siguiente_registro(obra_id, tipo):
    obra = Obra.query.get_or_404(obra_id)
    return render_template("obras/siguiente_registro.html", obra=obra, tipo=tipo)


# ─────────────────────────── Gastos (materiales, equipo, etc.) ───────────

@obras_bp.route("/<int:obra_id>/gastos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_gasto(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = GastoForm()
    form.proveedor_id.choices = [(0, "— Sin proveedor —")] + [
        (p.id, p.nombre) for p in Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    ]
    if form.validate_on_submit():
        db.session.add(Gasto(
            obra_id=obra.id, categoria=form.categoria.data, concepto=form.concepto.data,
            cantidad=form.cantidad.data, unidad=form.unidad.data, monto=form.monto.data,
            fecha=form.fecha.data, proveedor_id=form.proveedor_id.data or None,
            registrado_por=current_user.id,
        ))
        db.session.commit()
        flash("Gasto registrado.", "success")
        return _siguiente_registro(obra, "gasto")
    if request.method == "GET":
        form.fecha.data = date.today()
    return render_template("obras/gasto_form.html", form=form, obra=obra)


# ─────────────────────────── Mano de obra (albaniles, pintores, etc.) ────

@obras_bp.route("/<int:obra_id>/mano-de-obra/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_pago_mano_obra(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = PagoManoObraForm()
    form.trabajador_id.choices = [
        (t.id, f"{t.nombre} ({t.oficio})") for t in Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre).all()
    ]
    if not form.trabajador_id.choices:
        flash("Todavía no hay trabajadores registrados. Agrega uno primero.", "warning")
        return redirect(url_for("trabajadores.nuevo", obra_id=obra.id))

    if form.validate_on_submit():
        db.session.add(PagoManoObra(
            obra_id=obra.id, trabajador_id=form.trabajador_id.data, concepto=form.concepto.data,
            dias_o_unidades=form.dias_o_unidades.data, monto=form.monto.data, fecha=form.fecha.data,
            registrado_por=current_user.id,
        ))
        db.session.commit()
        flash("Pago de mano de obra registrado.", "success")
        return _siguiente_registro(obra, "mano_obra")
    if request.method == "GET":
        form.fecha.data = date.today()
    return render_template("obras/mano_obra_form.html", form=form, obra=obra)


# ─────────────────────────── Avance de obra ───────────────────────────────

@obras_bp.route("/<int:obra_id>/avance/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_avance(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = AvanceForm()
    if form.validate_on_submit():
        db.session.add(AvanceObra(
            obra_id=obra.id, semana=form.semana.data, etapa=form.etapa.data,
            porcentaje=form.porcentaje.data, descripcion=form.descripcion.data,
            reportado_por=current_user.id,
        ))
        obra.avance_porcentaje = form.porcentaje.data
        db.session.commit()
        flash("Avance registrado.", "success")
        return _siguiente_registro(obra, "avance")
    return render_template("obras/avance_form.html", form=form, obra=obra)


# ─────────────────────────── Tareas ───────────────────────────────────────

@obras_bp.route("/<int:obra_id>/tareas/nueva", methods=["GET", "POST"])
@login_required
def nueva_tarea(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = TareaForm()
    form.responsable_id.choices = [(0, "— Sin asignar —")] + [
        (u.id, u.nombre) for u in Usuario.query.filter_by(activo=True).order_by(Usuario.nombre).all()
    ]
    if form.validate_on_submit():
        db.session.add(Tarea(
            obra_id=obra.id, titulo=form.titulo.data, descripcion=form.descripcion.data,
            responsable_id=form.responsable_id.data or None, fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data, prioridad=form.prioridad.data, creado_por=current_user.id,
        ))
        db.session.commit()
        flash("Tarea creada.", "success")
        return _siguiente_registro(obra, "tarea")
    return render_template("obras/tarea_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/tareas/<int:tarea_id>/estado", methods=["POST"])
@login_required
def cambiar_estado_tarea(obra_id, tarea_id):
    tarea = Tarea.query.filter_by(id=tarea_id, obra_id=obra_id).first_or_404()
    nuevo_estado = request.form.get("estado")
    if nuevo_estado in ("pendiente", "en_curso", "terminada"):
        tarea.estado = nuevo_estado
        db.session.commit()
        flash("Tarea actualizada.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="tareas"))


# ─────────────────────────── Bitacora diaria ──────────────────────────────

@obras_bp.route("/<int:obra_id>/bitacora/nueva", methods=["GET", "POST"])
@login_required
def nueva_bitacora(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = BitacoraForm()
    if request.method == "GET":
        form.fecha.data = date.today()
    if form.validate_on_submit():
        ya_existe = BitacoraObra.query.filter_by(obra_id=obra.id, fecha=form.fecha.data).first()
        if ya_existe:
            flash("Ya existe un registro de bitácora para esa fecha.", "danger")
        else:
            db.session.add(BitacoraObra(
                obra_id=obra.id, fecha=form.fecha.data, clima=form.clima.data,
                personal_en_obra=form.personal_en_obra.data, actividades=form.actividades.data,
                incidencias=form.incidencias.data, registrado_por=current_user.id,
            ))
            db.session.commit()
            flash("Bitácora guardada.", "success")
            return _siguiente_registro(obra, "bitacora")
    return render_template("obras/bitacora_form.html", form=form, obra=obra)


# ─────────────────────────── Documentos ───────────────────────────────────

@obras_bp.route("/<int:obra_id>/documentos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_documento(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = DocumentoForm()
    if form.validate_on_submit():
        db.session.add(Documento(
            obra_id=obra.id, nombre=form.nombre.data, categoria=form.categoria.data,
            url_archivo=form.url_archivo.data, visible_cliente=form.visible_cliente.data,
            subido_por=current_user.id,
        ))
        db.session.commit()
        flash("Documento registrado.", "success")
        return _siguiente_registro(obra, "documento")
    return render_template("obras/documento_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/documentos/<int:documento_id>/visibilidad", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def toggle_visibilidad_documento(obra_id, documento_id):
    doc = Documento.query.filter_by(id=documento_id, obra_id=obra_id).first_or_404()
    doc.visible_cliente = not doc.visible_cliente
    db.session.commit()
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="documentos"))


# ─────────────────────────── Pagos del cliente ────────────────────────────

@obras_bp.route("/<int:obra_id>/pagos/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nuevo_pago_cliente(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = PagoClienteForm()
    if form.validate_on_submit():
        db.session.add(PagoCliente(
            obra_id=obra.id, concepto=form.concepto.data, monto=form.monto.data,
            fecha_programada=form.fecha_programada.data,
        ))
        db.session.commit()
        flash("Pago del cliente programado.", "success")
        return _siguiente_registro(obra, "pago_cliente")
    return render_template("obras/pago_cliente_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/pagos/<int:pago_id>/recibir", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def marcar_pago_recibido(obra_id, pago_id):
    pago = PagoCliente.query.filter_by(id=pago_id, obra_id=obra_id).first_or_404()
    pago.estado = "recibido"
    pago.fecha_recibido = date.today()
    db.session.commit()
    flash("Pago marcado como recibido.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="pagos"))
