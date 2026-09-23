import calendar
import csv
import io
from collections import OrderedDict
from datetime import date, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file, Response
from flask_login import login_required, current_user

from . import archivos, auditoria
from .alertas import verificar_presupuesto
from .extensions import db
from .decorators import roles_requeridos
from .forms import (
    GastoForm, PagoManoObraForm, AvanceForm, TareaForm, BitacoraForm,
    DocumentoForm, PagoClienteForm, MovimientoInventarioForm, OrdenCompraForm,
    OrdenCambioForm, IncidenteSeguridadForm, AsignacionEquipoForm,
    ContratoSubcontratistaForm, MensajeObraForm,
)
from .models import (
    Obra, Gasto, PagoManoObra, Trabajador, AvanceObra, Tarea, BitacoraObra, BitacoraFoto,
    Documento, PagoCliente, Proveedor, Usuario, Cliente, MovimientoInventario, OrdenCompra,
    OrdenCambio, IncidenteSeguridad, Equipo, AsignacionEquipo, Subcontratista,
    ContratoSubcontratista, MensajeObra, Asistencia,
)
from .notificaciones import notificar, notificar_cliente

obras_bp = Blueprint("obras", __name__)


@obras_bp.route("/")
@login_required
def lista():
    filtro = request.args.get("estado", "todas")
    texto = request.args.get("q", "").strip()
    responsable_id = request.args.get("responsable_id", type=int)
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    query = Obra.query
    if filtro != "todas":
        query = query.filter_by(estado=filtro)
    if texto:
        patron = f"%{texto}%"
        query = query.join(Obra.cliente).filter(db.or_(Obra.nombre.ilike(patron), Cliente.nombre.ilike(patron)))
    if responsable_id:
        query = query.filter_by(responsable_id=responsable_id)
    if desde:
        query = query.filter(Obra.fecha_inicio >= date.fromisoformat(desde))
    if hasta:
        query = query.filter(Obra.fecha_inicio <= date.fromisoformat(hasta))

    obras = query.order_by(Obra.creado_en.desc()).all()
    responsables = Usuario.query.filter_by(activo=True).order_by(Usuario.nombre).all()
    return render_template(
        "obras/lista.html", obras=obras, filtro=filtro, texto=texto,
        responsable_id=responsable_id, desde=desde or "", hasta=hasta or "", responsables=responsables,
    )


def _flujo_caja(obra):
    """Agrega ingresos (pagos de cliente recibidos) y egresos (gastos + mano
    de obra) por mes calendario, para la grafica de flujo de caja."""
    meses = OrderedDict()

    def _clave(fecha):
        return f"{fecha.year}-{fecha.month:02d}"

    def _sumar(fecha, campo, monto):
        clave = _clave(fecha)
        meses.setdefault(clave, {"ingresos": 0, "egresos": 0})
        meses[clave][campo] += float(monto)

    for g in obra.gastos:
        _sumar(g.fecha, "egresos", g.monto)
    for p in obra.pagos_mano_obra:
        _sumar(p.fecha, "egresos", p.monto)
    for p in obra.pagos_cliente:
        if p.fecha_recibido:
            _sumar(p.fecha_recibido, "ingresos", p.monto)

    claves_ordenadas = sorted(meses.keys())
    etiquetas = []
    for clave in claves_ordenadas:
        anio, mes = clave.split("-")
        etiquetas.append(f"{calendar.month_abbr[int(mes)]} {anio}")

    return {
        "etiquetas": etiquetas,
        "ingresos": [round(meses[c]["ingresos"], 2) for c in claves_ordenadas],
        "egresos": [round(meses[c]["egresos"], 2) for c in claves_ordenadas],
    }


@obras_bp.route("/<int:obra_id>")
@login_required
def detalle(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    return render_template("obras/detalle.html", obra=obra, flujo_caja=_flujo_caja(obra))


def _curva_s(obra):
    """Avance fisico (% reportado) vs avance financiero (% del contrato ya
    gastado) en cada fecha de avance — detecta obras que gastan mas rapido
    de lo que avanzan."""
    if not obra.monto_contrato:
        return {"etiquetas": [], "fisico": [], "financiero": []}

    avances = sorted(obra.avances, key=lambda a: a.semana)
    etiquetas, fisico, financiero = [], [], []
    for a in avances:
        gasto_a_la_fecha = sum((g.monto for g in obra.gastos if g.fecha <= a.semana), start=0)
        gasto_a_la_fecha += sum((p.monto for p in obra.pagos_mano_obra if p.fecha <= a.semana), start=0)
        etiquetas.append(a.semana.strftime("%d/%m"))
        fisico.append(a.porcentaje)
        financiero.append(round(float(gasto_a_la_fecha) / float(obra.monto_contrato) * 100, 1))
    return {"etiquetas": etiquetas, "fisico": fisico, "financiero": financiero}


@obras_bp.route("/<int:obra_id>/gastos/exportar.csv")
@login_required
@roles_requeridos("admin", "supervisor")
def exportar_gastos_csv(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["Fecha", "Categoría", "Concepto", "Cantidad", "Unidad", "Monto", "Proveedor"])
    for g in obra.gastos:
        escritor.writerow([g.fecha.isoformat(), g.categoria, g.concepto, g.cantidad or "", g.unidad or "", f"{g.monto:.2f}", g.proveedor.nombre if g.proveedor else ""])
    for p in obra.pagos_mano_obra:
        escritor.writerow([p.fecha.isoformat(), "mano_obra", f"{p.concepto} ({p.trabajador.nombre})", p.dias_o_unidades or "", "", f"{p.monto:.2f}", ""])
    return Response(
        salida.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=gastos_obra_{obra.id}.csv"},
    )


@obras_bp.route("/<int:obra_id>/reporte-cierre")
@login_required
@roles_requeridos("admin", "supervisor")
def reporte_cierre(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    total_recibido = sum((p.monto for p in obra.pagos_cliente if p.estado == "recibido"), start=0)
    total_pendiente = sum((p.monto for p in obra.pagos_cliente if p.estado in ("pendiente", "vencido")), start=0)
    margen = (obra.monto_contrato or 0) - obra.gasto_real
    margen_pct = round(float(margen) / float(obra.monto_contrato) * 100, 1) if obra.monto_contrato else 0
    return render_template(
        "obras/reporte_cierre.html", obra=obra,
        total_recibido=total_recibido, total_pendiente=total_pendiente,
        margen=margen, margen_pct=margen_pct, curva_s=_curva_s(obra),
    )


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
        verificar_presupuesto(obra)
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
        verificar_presupuesto(obra)
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
        notificar_cliente(
            obra.cliente.email, f"Nuevo avance en tu obra: {obra.nombre}",
            f"Etapa: {form.etapa.data}\nAvance acumulado: {form.porcentaje.data}%\n{form.descripcion.data or ''}",
        )
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
            bitacora = BitacoraObra(
                obra_id=obra.id, fecha=form.fecha.data, clima=form.clima.data,
                personal_en_obra=form.personal_en_obra.data, actividades=form.actividades.data,
                incidencias=form.incidencias.data, registrado_por=current_user.id,
            )
            db.session.add(bitacora)
            db.session.flush()
            for foto in form.fotos.data or []:
                if foto and foto.filename:
                    ruta = archivos.guardar_archivo(foto, f"bitacora/{obra.id}")
                    db.session.add(BitacoraFoto(bitacora_id=bitacora.id, ruta_archivo=ruta))
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
        archivo = form.archivo.data
        if archivo and archivo.filename:
            referencia = archivos.guardar_archivo(archivo, f"documentos/{obra.id}")
        elif form.url_archivo.data:
            referencia = form.url_archivo.data
        else:
            flash("Sube un archivo o captura una URL/ruta externa.", "danger")
            return render_template("obras/documento_form.html", form=form, obra=obra)

        db.session.add(Documento(
            obra_id=obra.id, nombre=form.nombre.data, categoria=form.categoria.data,
            url_archivo=referencia, visible_cliente=form.visible_cliente.data,
            fecha_vencimiento=form.fecha_vencimiento.data,
            subido_por=current_user.id,
        ))
        db.session.commit()
        if form.visible_cliente.data:
            notificar_cliente(
                obra.cliente.email, f"Nuevo documento disponible: {obra.nombre}",
                f"Se agregó el documento '{form.nombre.data}' a tu portal.",
            )
        flash("Documento registrado.", "success")
        return _siguiente_registro(obra, "documento")
    return render_template("obras/documento_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/documentos/<int:documento_id>/descargar")
@login_required
def descargar_documento(obra_id, documento_id):
    doc = Documento.query.filter_by(id=documento_id, obra_id=obra_id).first_or_404()
    if current_user.tipo == "cliente":
        if current_user.cliente_id != doc.obra.cliente_id or not doc.visible_cliente:
            abort(403)
    if not archivos.es_local(doc.url_archivo):
        return redirect(doc.url_archivo)
    return send_file(archivos.ruta_absoluta_de(doc.url_archivo), download_name=doc.nombre, as_attachment=True)


@obras_bp.route("/<int:obra_id>/bitacora/fotos/<int:foto_id>")
@login_required
def ver_foto_bitacora(obra_id, foto_id):
    foto = BitacoraFoto.query.join(BitacoraObra).filter(
        BitacoraFoto.id == foto_id, BitacoraObra.obra_id == obra_id,
    ).first_or_404()
    if current_user.tipo == "cliente" and current_user.cliente_id != foto.bitacora.obra.cliente_id:
        abort(403)
    return send_file(archivos.ruta_absoluta_de(foto.ruta_archivo))


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


# ─────────────────────────── Inventario de materiales ─────────────────────

@obras_bp.route("/<int:obra_id>/inventario/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_movimiento_inventario(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = MovimientoInventarioForm()
    if request.method == "GET":
        form.fecha.data = date.today()
    if form.validate_on_submit():
        db.session.add(MovimientoInventario(
            obra_id=obra.id, tipo=form.tipo.data, material=form.material.data,
            unidad=form.unidad.data, cantidad=form.cantidad.data, motivo=form.motivo.data,
            fecha=form.fecha.data, registrado_por=current_user.id,
        ))
        db.session.commit()
        flash("Movimiento de inventario registrado.", "success")
        return redirect(url_for("obras.detalle", obra_id=obra.id, _anchor="inventario"))
    return render_template("obras/inventario_form.html", form=form, obra=obra)


# ─────────────────────────── Ordenes de compra ─────────────────────────────

@obras_bp.route("/<int:obra_id>/compras/nueva", methods=["GET", "POST"])
@login_required
def nueva_orden_compra(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = OrdenCompraForm()
    form.proveedor_id.choices = [(0, "— Sin proveedor —")] + [
        (p.id, p.nombre) for p in Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all()
    ]
    if request.method == "GET":
        form.fecha_solicitud.data = date.today()
    if form.validate_on_submit():
        db.session.add(OrdenCompra(
            obra_id=obra.id, proveedor_id=form.proveedor_id.data or None, concepto=form.concepto.data,
            cantidad=form.cantidad.data, unidad=form.unidad.data, costo_estimado=form.costo_estimado.data,
            fecha_solicitud=form.fecha_solicitud.data, creado_por=current_user.id,
        ))
        db.session.commit()
        flash("Orden de compra creada.", "success")
        return redirect(url_for("obras.detalle", obra_id=obra.id, _anchor="compras"))
    return render_template("obras/orden_compra_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/compras/<int:orden_id>/confirmar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def confirmar_orden_compra(obra_id, orden_id):
    orden = OrdenCompra.query.filter_by(id=orden_id, obra_id=obra_id).first_or_404()
    if orden.estado == "solicitada":
        orden.estado = "confirmada"
        db.session.commit()
        flash("Orden de compra confirmada con el proveedor.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="compras"))


@obras_bp.route("/<int:obra_id>/compras/<int:orden_id>/recibir", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def recibir_orden_compra(obra_id, orden_id):
    """Al recibirse: genera el Gasto real (a diferencia del costo estimado) y
    la entrada de inventario correspondiente, en una sola accion."""
    orden = OrdenCompra.query.filter_by(id=orden_id, obra_id=obra_id).first_or_404()
    if orden.estado not in ("solicitada", "confirmada"):
        flash("Esta orden ya no se puede marcar como recibida.", "danger")
        return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="compras"))

    gasto = Gasto(
        obra_id=orden.obra_id, categoria="materiales", concepto=orden.concepto,
        cantidad=orden.cantidad, unidad=orden.unidad, monto=orden.costo_estimado,
        fecha=date.today(), proveedor_id=orden.proveedor_id, registrado_por=current_user.id,
    )
    db.session.add(gasto)
    db.session.flush()

    db.session.add(MovimientoInventario(
        obra_id=orden.obra_id, tipo="entrada", material=orden.concepto, unidad=orden.unidad,
        cantidad=orden.cantidad, motivo=f"Recepción de orden de compra #{orden.id}",
        fecha=date.today(), registrado_por=current_user.id,
    ))

    orden.estado = "recibida"
    orden.fecha_recibido = date.today()
    orden.gasto_generado_id = gasto.id
    db.session.commit()
    verificar_presupuesto(orden.obra)
    flash("Orden recibida: se registró el gasto y entró al inventario.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="compras"))


@obras_bp.route("/<int:obra_id>/compras/<int:orden_id>/cancelar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def cancelar_orden_compra(obra_id, orden_id):
    orden = OrdenCompra.query.filter_by(id=orden_id, obra_id=obra_id).first_or_404()
    if orden.estado in ("solicitada", "confirmada"):
        orden.estado = "cancelada"
        db.session.commit()
        flash("Orden de compra cancelada.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="compras"))


# ─────────────────────────── Ordenes de cambio (adenda de contrato) ───────

@obras_bp.route("/<int:obra_id>/cambios/nueva", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nueva_orden_cambio(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = OrdenCambioForm()
    if form.validate_on_submit():
        db.session.add(OrdenCambio(
            obra_id=obra.id, descripcion=form.descripcion.data, monto=form.monto.data,
            creado_por=current_user.id,
        ))
        db.session.commit()
        flash("Orden de cambio registrada, pendiente de aprobación.", "success")
        return redirect(url_for("obras.detalle", obra_id=obra.id, _anchor="cambios"))
    return render_template("obras/orden_cambio_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/cambios/<int:orden_id>/resolver", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def resolver_orden_cambio(obra_id, orden_id):
    """Unico camino para que una orden de cambio mueva Obra.monto_contrato —
    aprobarla lo hace de forma trazable, nunca se edita el campo a mano."""
    orden = OrdenCambio.query.filter_by(id=orden_id, obra_id=obra_id).first_or_404()
    decision = request.form.get("decision")
    if orden.estado != "pendiente" or decision not in ("aprobada", "rechazada"):
        abort(400)

    orden.estado = decision
    orden.resuelta_en = datetime.utcnow()
    if decision == "aprobada":
        orden.obra.monto_contrato = (orden.obra.monto_contrato or 0) + orden.monto
        auditoria.registrar(
            "aprobar_orden_cambio", "obra", orden.obra_id,
            f"Orden de cambio #{orden.id} (+${orden.monto:,.2f}): {orden.descripcion[:200]}",
        )
    db.session.commit()
    flash(f"Orden de cambio {decision}.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="cambios"))


# ─────────────────────────── Seguridad e higiene ───────────────────────────

@obras_bp.route("/<int:obra_id>/seguridad/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_incidente_seguridad(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = IncidenteSeguridadForm()
    if request.method == "GET":
        form.fecha.data = date.today()
    if form.validate_on_submit():
        db.session.add(IncidenteSeguridad(
            obra_id=obra.id, fecha=form.fecha.data, tipo=form.tipo.data, gravedad=form.gravedad.data,
            descripcion=form.descripcion.data, accion_tomada=form.accion_tomada.data,
            registrado_por=current_user.id,
        ))
        db.session.commit()
        if form.tipo.data != "checklist_epp" and form.gravedad.data == "alta":
            notificar(
                f"🚨 Incidente de seguridad grave — {obra.nombre}",
                f"{form.descripcion.data}\nAcción tomada: {form.accion_tomada.data or 'pendiente'}",
            )
        flash("Registro de seguridad guardado.", "success")
        return redirect(url_for("obras.detalle", obra_id=obra.id, _anchor="seguridad"))
    return render_template("obras/incidente_seguridad_form.html", form=form, obra=obra)


# ─────────────────────────── Asistencia diaria ─────────────────────────────

@obras_bp.route("/<int:obra_id>/asistencia", methods=["GET", "POST"])
@login_required
def asistencia(obra_id):
    """Checklist del dia: quien de los trabajadores activos llego a esta obra
    — independiente de PagoManoObra, que registra el pago, no la asistencia."""
    obra = Obra.query.get_or_404(obra_id)
    fecha_str = request.values.get("fecha")
    fecha = date.fromisoformat(fecha_str) if fecha_str else date.today()
    trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre).all()

    if request.method == "POST":
        for t in trabajadores:
            presente = request.form.get(f"presente_{t.id}") == "on"
            registro = Asistencia.query.filter_by(trabajador_id=t.id, fecha=fecha).first()
            if registro:
                registro.presente = presente
                registro.obra_id = obra.id
            elif presente:
                db.session.add(Asistencia(
                    trabajador_id=t.id, obra_id=obra.id, fecha=fecha,
                    presente=True, registrado_por=current_user.id,
                ))
        db.session.commit()
        flash(f"Asistencia del {fecha.strftime('%d/%m/%Y')} guardada.", "success")
        return redirect(url_for("obras.asistencia", obra_id=obra.id, fecha=fecha.isoformat()))

    registros = {a.trabajador_id: a.presente for a in Asistencia.query.filter_by(fecha=fecha).all()}
    return render_template("obras/asistencia.html", obra=obra, trabajadores=trabajadores, fecha=fecha, registros=registros)


# ─────────────────────────── Equipo asignado a la obra ─────────────────────

@obras_bp.route("/<int:obra_id>/equipo/asignar", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def asignar_equipo(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = AsignacionEquipoForm()
    form.equipo_id.choices = [(e.id, e.nombre) for e in Equipo.query.filter_by(activo=True).order_by(Equipo.nombre).all()]
    if not form.equipo_id.choices:
        flash("Todavía no hay equipo registrado. Agrega uno primero.", "warning")
        return redirect(url_for("equipo.nuevo"))
    if request.method == "GET":
        form.fecha_inicio.data = date.today()
    if form.validate_on_submit():
        db.session.add(AsignacionEquipo(
            obra_id=obra.id, equipo_id=form.equipo_id.data,
            fecha_inicio=form.fecha_inicio.data, notas=form.notas.data,
        ))
        db.session.commit()
        flash("Equipo asignado a la obra.", "success")
        return redirect(url_for("obras.detalle", obra_id=obra.id, _anchor="equipo"))
    return render_template("obras/asignar_equipo_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/equipo/<int:asignacion_id>/liberar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def liberar_equipo(obra_id, asignacion_id):
    asignacion = AsignacionEquipo.query.filter_by(id=asignacion_id, obra_id=obra_id).first_or_404()
    asignacion.fecha_fin = date.today()
    db.session.commit()
    flash("Equipo liberado de la obra.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="equipo"))


# ─────────────────────────── Subcontratistas en la obra ────────────────────

@obras_bp.route("/<int:obra_id>/subcontratos/nuevo", methods=["GET", "POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def nuevo_contrato_subcontratista(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = ContratoSubcontratistaForm()
    form.subcontratista_id.choices = [
        (s.id, s.nombre) for s in Subcontratista.query.filter_by(activo=True).order_by(Subcontratista.nombre).all()
    ]
    if not form.subcontratista_id.choices:
        flash("Todavía no hay subcontratistas registrados. Agrega uno primero.", "warning")
        return redirect(url_for("subcontratistas.nuevo"))
    if form.validate_on_submit():
        db.session.add(ContratoSubcontratista(
            obra_id=obra.id, subcontratista_id=form.subcontratista_id.data, concepto=form.concepto.data,
            monto=form.monto.data, fecha_inicio=form.fecha_inicio.data, fecha_fin=form.fecha_fin.data,
        ))
        db.session.commit()
        flash("Contrato de subcontratista registrado.", "success")
        return redirect(url_for("obras.detalle", obra_id=obra.id, _anchor="subcontratos"))
    return render_template("obras/contrato_subcontratista_form.html", form=form, obra=obra)


@obras_bp.route("/<int:obra_id>/subcontratos/<int:contrato_id>/avance", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def actualizar_avance_subcontrato(obra_id, contrato_id):
    contrato = ContratoSubcontratista.query.filter_by(id=contrato_id, obra_id=obra_id).first_or_404()
    porcentaje = request.form.get("avance_porcentaje", type=int)
    if porcentaje is not None and 0 <= porcentaje <= 100:
        contrato.avance_porcentaje = porcentaje
        if porcentaje == 100:
            contrato.estado = "terminado"
        db.session.commit()
        flash("Avance del subcontrato actualizado.", "success")
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="subcontratos"))


# ─────────────────────────── Mensajeria con el cliente ─────────────────────

@obras_bp.route("/<int:obra_id>/mensajes/nuevo", methods=["POST"])
@login_required
def nuevo_mensaje(obra_id):
    obra = Obra.query.get_or_404(obra_id)
    form = MensajeObraForm()
    if form.validate_on_submit():
        db.session.add(MensajeObra(
            obra_id=obra.id, autor_tipo="usuario", autor_nombre=current_user.nombre, texto=form.texto.data,
        ))
        db.session.commit()
    return redirect(url_for("obras.detalle", obra_id=obra_id, _anchor="mensajes"))
