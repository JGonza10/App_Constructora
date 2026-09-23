import csv
import io
from collections import defaultdict
from datetime import date, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required

from . import archivos
from .decorators import roles_requeridos
from .extensions import db
from .forms import TrabajadorForm, DocumentoTrabajadorForm, AusenciaTrabajadorForm
from .models import Trabajador, PagoManoObra, Asistencia, DocumentoTrabajador, AusenciaTrabajador

trabajadores_bp = Blueprint("trabajadores", __name__)


@trabajadores_bp.route("/")
@login_required
def lista():
    trabajadores = Trabajador.query.filter_by(activo=True).order_by(Trabajador.nombre).all()
    return render_template("trabajadores/lista.html", trabajadores=trabajadores)


@trabajadores_bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = TrabajadorForm()
    obra_id = request.args.get("obra_id", type=int)
    if form.validate_on_submit():
        db.session.add(Trabajador(
            nombre=form.nombre.data, oficio=form.oficio.data,
            telefono=form.telefono.data, tipo_pago=form.tipo_pago.data,
        ))
        db.session.commit()
        flash(f"Trabajador '{form.nombre.data}' registrado.", "success")
        if obra_id:
            return redirect(url_for("obras.nuevo_pago_mano_obra", obra_id=obra_id))
        return redirect(url_for("trabajadores.lista"))
    return render_template("trabajadores/form.html", form=form, obra_id=obra_id)


@trabajadores_bp.route("/<int:trabajador_id>")
@login_required
def detalle(trabajador_id):
    trabajador = Trabajador.query.get_or_404(trabajador_id)
    return render_template("trabajadores/detalle.html", trabajador=trabajador, hoy=date.today())


@trabajadores_bp.route("/<int:trabajador_id>/documentos/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_documento(trabajador_id):
    trabajador = Trabajador.query.get_or_404(trabajador_id)
    form = DocumentoTrabajadorForm()
    if form.validate_on_submit():
        ruta = archivos.guardar_archivo(form.archivo.data, f"trabajadores/{trabajador.id}")
        db.session.add(DocumentoTrabajador(
            trabajador_id=trabajador.id, nombre=form.nombre.data, categoria=form.categoria.data,
            ruta_archivo=ruta, fecha_vencimiento=form.fecha_vencimiento.data,
        ))
        db.session.commit()
        flash("Documento agregado al expediente.", "success")
        return redirect(url_for("trabajadores.detalle", trabajador_id=trabajador.id))
    return render_template("trabajadores/documento_form.html", form=form, trabajador=trabajador)


@trabajadores_bp.route("/documentos/<int:documento_id>/descargar")
@login_required
def descargar_documento(documento_id):
    from flask import send_file
    doc = DocumentoTrabajador.query.get_or_404(documento_id)
    return send_file(archivos.ruta_absoluta_de(doc.ruta_archivo), download_name=doc.nombre, as_attachment=True)


@trabajadores_bp.route("/<int:trabajador_id>/ausencias/nueva", methods=["GET", "POST"])
@login_required
def nueva_ausencia(trabajador_id):
    trabajador = Trabajador.query.get_or_404(trabajador_id)
    form = AusenciaTrabajadorForm()
    if form.validate_on_submit():
        db.session.add(AusenciaTrabajador(
            trabajador_id=trabajador.id, tipo=form.tipo.data,
            fecha_inicio=form.fecha_inicio.data, fecha_fin=form.fecha_fin.data, motivo=form.motivo.data,
        ))
        db.session.commit()
        flash("Ausencia registrada.", "success")
        return redirect(url_for("trabajadores.detalle", trabajador_id=trabajador.id))
    return render_template("trabajadores/ausencia_form.html", form=form, trabajador=trabajador)


@trabajadores_bp.route("/nomina")
@login_required
def nomina():
    """Agrupa los pagos de mano de obra por trabajador dentro de la semana
    (lunes-domingo) pedida, sin importar en que obra se hayan hecho."""
    semana_param = request.args.get("semana")
    if semana_param:
        try:
            fecha_ref = date.fromisoformat(semana_param)
        except ValueError:
            fecha_ref = date.today()
    else:
        fecha_ref = date.today()

    lunes = fecha_ref - timedelta(days=fecha_ref.weekday())
    domingo = lunes + timedelta(days=6)
    filas = _filas_nomina(lunes, domingo)
    total_semana = sum((f["total"] for f in filas), start=0)

    return render_template(
        "trabajadores/nomina.html", filas=filas, total_semana=total_semana,
        lunes=lunes, domingo=domingo,
        semana_anterior=(lunes - timedelta(days=7)).isoformat(),
        semana_siguiente=(lunes + timedelta(days=7)).isoformat(),
    )


def _filas_nomina(lunes, domingo):
    pagos = PagoManoObra.query.filter(
        PagoManoObra.fecha >= lunes, PagoManoObra.fecha <= domingo,
    ).order_by(PagoManoObra.fecha).all()
    asistencias = Asistencia.query.filter(
        Asistencia.fecha >= lunes, Asistencia.fecha <= domingo, Asistencia.presente.is_(True),
    ).all()
    ausencias_activas = AusenciaTrabajador.query.filter(
        AusenciaTrabajador.fecha_inicio <= domingo, AusenciaTrabajador.fecha_fin >= lunes,
    ).all()

    pagos_por_trabajador_id = defaultdict(list)
    for p in pagos:
        pagos_por_trabajador_id[p.trabajador_id].append(p)
    dias_por_trabajador_id = defaultdict(int)
    for a in asistencias:
        dias_por_trabajador_id[a.trabajador_id] += 1
    ausencia_por_trabajador_id = {a.trabajador_id: a for a in ausencias_activas}

    ids_con_actividad = set(pagos_por_trabajador_id) | set(dias_por_trabajador_id) | set(ausencia_por_trabajador_id)
    trabajadores = Trabajador.query.filter(Trabajador.id.in_(ids_con_actividad)).order_by(Trabajador.nombre).all() if ids_con_actividad else []

    filas = []
    for trabajador in trabajadores:
        pagos_trab = pagos_por_trabajador_id.get(trabajador.id, [])
        filas.append({
            "trabajador": trabajador, "pagos": pagos_trab,
            "total": sum((p.monto for p in pagos_trab), start=0),
            "dias_asistidos": dias_por_trabajador_id.get(trabajador.id, 0),
            "ausencia": ausencia_por_trabajador_id.get(trabajador.id),
        })
    return filas


@trabajadores_bp.route("/nomina/exportar.csv")
@login_required
@roles_requeridos("admin", "supervisor")
def nomina_exportar_csv():
    semana_param = request.args.get("semana")
    fecha_ref = date.fromisoformat(semana_param) if semana_param else date.today()
    lunes = fecha_ref - timedelta(days=fecha_ref.weekday())
    domingo = lunes + timedelta(days=6)
    filas = _filas_nomina(lunes, domingo)

    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["Trabajador", "Oficio", "Días asistidos", "Total pagado"])
    for f in filas:
        escritor.writerow([f["trabajador"].nombre, f["trabajador"].oficio, f["dias_asistidos"], f"{f['total']:.2f}"])

    return Response(
        salida.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=nomina_{lunes.isoformat()}.csv"},
    )
