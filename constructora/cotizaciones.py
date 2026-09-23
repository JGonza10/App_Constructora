import base64
import json
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import login_required, current_user

from . import archivos, auditoria
from .extensions import db
from .decorators import roles_requeridos
from .forms import CotizacionForm, RechazoCotizacionForm, AceptarCotizacionForm
from .models import Cotizacion, CotizacionItem, ConceptoCatalogo, PlantillaCotizacion, Levantamiento, Obra, Usuario
from .pdf import generar_pdf_cotizacion

cotizaciones_bp = Blueprint("cotizaciones", __name__)


def _contexto_catalogo():
    conceptos = ConceptoCatalogo.query.filter_by(activo=True).order_by(ConceptoCatalogo.concepto).all()
    catalogo_json = json.dumps({
        str(c.id): {"concepto": c.concepto, "unidad": c.unidad, "precio_unitario": str(c.precio_unitario)}
        for c in conceptos
    })
    plantillas = PlantillaCotizacion.query.order_by(PlantillaCotizacion.nombre).all()
    return {"catalogo": conceptos, "catalogo_json": catalogo_json, "plantillas": plantillas}


def guardar_firma_cotizacion(cotizacion, firma_data_url):
    """firma_data_url viene de un <canvas>.toDataURL() del cliente en el
    portal: 'data:image/png;base64,....'. Si no se capturo firma, no hace nada."""
    if not firma_data_url or "base64," not in firma_data_url:
        return
    contenido = base64.b64decode(firma_data_url.split("base64,", 1)[1])
    cotizacion.firma_url = archivos.guardar_bytes(contenido, "png", f"firmas/{cotizacion.id}")


def crear_obra_desde_cotizacion(cotizacion, responsable_id=None, fecha_inicio=None, fecha_fin_estimada=None, firma_data_url=None):
    """Unico camino para que nazca una Obra (ver CLAUDE.md) — lo usan tanto la
    aceptacion interna como la aceptacion del cliente desde el portal."""
    levantamiento = cotizacion.levantamiento
    cotizacion.estado = "aceptada"
    cotizacion.respondida_en = datetime.utcnow()
    guardar_firma_cotizacion(cotizacion, firma_data_url)
    levantamiento.estado = "cotizado"

    obra = Obra(
        cotizacion_id=cotizacion.id,
        cliente_id=levantamiento.cliente_id,
        nombre=levantamiento.titulo,
        tipo=levantamiento.tipo_obra,
        monto_contrato=cotizacion.total,
        responsable_id=responsable_id,
        fecha_inicio=fecha_inicio,
        fecha_fin_estimada=fecha_fin_estimada,
        direccion=levantamiento.direccion,
        descripcion=levantamiento.indicaciones_cliente,
    )
    db.session.add(obra)
    db.session.flush()
    auditoria.registrar("aceptar_cotizacion", "cotizacion", cotizacion.id, f"Nace obra #{obra.id} '{obra.nombre}' por ${obra.monto_contrato:,.2f}")
    db.session.commit()
    return obra


def rechazar_cotizacion(cotizacion, motivo):
    cotizacion.estado = "rechazada"
    cotizacion.motivo_rechazo = motivo
    cotizacion.respondida_en = datetime.utcnow()
    auditoria.registrar("rechazar_cotizacion", "cotizacion", cotizacion.id, motivo)
    db.session.commit()


@cotizaciones_bp.route("/levantamiento/<int:levantamiento_id>/nueva", methods=["GET", "POST"])
@login_required
def nueva(levantamiento_id):
    levantamiento = Levantamiento.query.get_or_404(levantamiento_id)
    form = CotizacionForm()

    if request.method == "POST" and request.form.get("accion") == "agregar_linea":
        form.items.append_entry()
        return render_template("cotizaciones/form.html", form=form, levantamiento=levantamiento, **_contexto_catalogo())

    if request.method == "POST" and request.form.get("accion") == "cargar_plantilla":
        plantilla = PlantillaCotizacion.query.get(request.form.get("plantilla_id", type=int))
        if plantilla and plantilla.items:
            while len(form.items.entries) > 0:
                form.items.pop_entry()
            for it in plantilla.items:
                form.items.append_entry({
                    "concepto": it.concepto, "unidad": it.unidad,
                    "cantidad": it.cantidad, "precio_unitario": it.precio_unitario,
                })
            if not form.titulo.data:
                form.titulo.data = plantilla.nombre
        return render_template("cotizaciones/form.html", form=form, levantamiento=levantamiento, **_contexto_catalogo())

    if form.validate_on_submit():
        items_validos = [
            it for it in form.items.entries
            if it.form.concepto.data and it.form.precio_unitario.data
        ]
        if not items_validos:
            flash("Agrega al menos un concepto con precio antes de guardar.", "warning")
            return render_template("cotizaciones/form.html", form=form, levantamiento=levantamiento, **_contexto_catalogo())

        cotizacion = Cotizacion(
            levantamiento_id=levantamiento.id,
            version=levantamiento.siguiente_version,
            titulo=form.titulo.data.strip(),
            notas=form.notas.data,
            creado_por=current_user.id,
        )
        db.session.add(cotizacion)
        for it in items_validos:
            cotizacion.items.append(CotizacionItem(
                concepto=it.form.concepto.data,
                unidad=it.form.unidad.data,
                cantidad=it.form.cantidad.data,
                precio_unitario=it.form.precio_unitario.data,
            ))
        levantamiento.estado = "en_cotizacion"
        db.session.commit()
        flash(f"Cotización v{cotizacion.version} guardada como borrador.", "success")
        return redirect(url_for("cotizaciones.detalle", cotizacion_id=cotizacion.id))

    return render_template("cotizaciones/form.html", form=form, levantamiento=levantamiento, **_contexto_catalogo())


@cotizaciones_bp.route("/<int:cotizacion_id>")
@login_required
def detalle(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    return render_template(
        "cotizaciones/detalle.html",
        cotizacion=cotizacion,
        form_rechazo=RechazoCotizacionForm(),
        form_aceptar=_form_aceptar(),
    )


def _form_aceptar():
    form = AceptarCotizacionForm()
    form.responsable_id.choices = [(0, "— Sin asignar por ahora —")] + [
        (u.id, u.nombre) for u in Usuario.query.filter_by(activo=True).order_by(Usuario.nombre).all()
    ]
    return form


@cotizaciones_bp.route("/<int:cotizacion_id>/enviar", methods=["POST"])
@login_required
def enviar(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    if cotizacion.estado != "borrador":
        abort(400)
    cotizacion.estado = "enviada"
    db.session.commit()
    flash("Cotización marcada como enviada al cliente.", "success")
    return redirect(url_for("cotizaciones.detalle", cotizacion_id=cotizacion.id))


@cotizaciones_bp.route("/<int:cotizacion_id>/rechazar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def rechazar(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    form = RechazoCotizacionForm()
    if cotizacion.estado != "enviada" or not form.validate_on_submit():
        flash("No se pudo registrar el rechazo.", "danger")
        return redirect(url_for("cotizaciones.detalle", cotizacion_id=cotizacion.id))

    rechazar_cotizacion(cotizacion, form.motivo_rechazo.data)
    flash("Cotización rechazada. Puedes crear una nueva versión desde el levantamiento.", "warning")
    return redirect(url_for("levantamientos.detalle", levantamiento_id=cotizacion.levantamiento_id))


@cotizaciones_bp.route("/<int:cotizacion_id>/aceptar", methods=["POST"])
@login_required
@roles_requeridos("admin", "supervisor")
def aceptar(cotizacion_id):
    """El paso que resuelve la queja original: aqui nace la Obra, con el monto
    de contrato heredado de la cotizacion aceptada — nunca se vuelve a teclear."""
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    if cotizacion.estado != "enviada":
        flash("Solo se puede aceptar una cotización que ya fue enviada.", "danger")
        return redirect(url_for("cotizaciones.detalle", cotizacion_id=cotizacion.id))

    form = _form_aceptar()
    if not form.validate_on_submit():
        flash("Revisa los datos de la obra a crear.", "danger")
        return redirect(url_for("cotizaciones.detalle", cotizacion_id=cotizacion.id))

    obra = crear_obra_desde_cotizacion(
        cotizacion,
        responsable_id=form.responsable_id.data or None,
        fecha_inicio=form.fecha_inicio.data,
        fecha_fin_estimada=form.fecha_fin_estimada.data,
    )
    flash(f"¡Obra '{obra.nombre}' creada! El contrato quedó en ${obra.monto_contrato:,.2f}, tomado directo de la cotización.", "success")
    return redirect(url_for("obras.siguiente_paso", obra_id=obra.id))


@cotizaciones_bp.route("/<int:cotizacion_id>/pdf")
@login_required
def pdf(cotizacion_id):
    cotizacion = Cotizacion.query.get_or_404(cotizacion_id)
    buffer = generar_pdf_cotizacion(cotizacion)
    nombre = f"cotizacion_{cotizacion.id}_v{cotizacion.version}.pdf"
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=nombre)


@cotizaciones_bp.route("/levantamiento/<int:levantamiento_id>/comparar")
@login_required
def comparar_versiones(levantamiento_id):
    levantamiento = Levantamiento.query.get_or_404(levantamiento_id)
    return render_template("cotizaciones/comparar.html", levantamiento=levantamiento)
