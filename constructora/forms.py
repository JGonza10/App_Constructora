from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField, DecimalField,
    IntegerField, DateField, BooleanField, FieldList, FormField, MultipleFileField,
)
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length

EXTENSIONES_DOCUMENTO = ["pdf", "png", "jpg", "jpeg", "webp", "gif", "doc", "docx", "xls", "xlsx", "dwg"]
EXTENSIONES_FOTO = ["png", "jpg", "jpeg", "webp"]


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])


class PortalLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])


class UsuarioForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8, message="Mínimo 8 caracteres")])
    rol = SelectField("Rol", choices=[("admin", "Admin"), ("supervisor", "Supervisor"), ("empleado", "Empleado")])


class ClienteForm(FlaskForm):
    nombre = StringField("Nombre completo / Razón social", validators=[DataRequired(), Length(max=150)])
    tipo = SelectField("Tipo", choices=[("persona_fisica", "Persona física"), ("empresa", "Empresa")])
    email = StringField("Email", validators=[Optional(), Email()])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=20)])
    rfc = StringField("RFC", validators=[Optional(), Length(max=20)])
    direccion = TextAreaField("Dirección", validators=[Optional()])
    notas = TextAreaField("Notas", validators=[Optional()])


class LevantamientoForm(FlaskForm):
    cliente_id = SelectField("Cliente", coerce=int, validators=[DataRequired()])
    titulo = StringField("Título del proyecto", validators=[DataRequired(), Length(max=150)])
    tipo_obra = SelectField("Tipo de obra", choices=[
        ("residencial", "Residencial"), ("comercial", "Comercial"),
        ("publica", "Pública"), ("mixta", "Mixta"), ("otro", "Otro"),
    ])
    direccion = TextAreaField("Dirección de la obra", validators=[Optional()])
    indicaciones_cliente = TextAreaField(
        "¿Qué pidió el cliente? (indicaciones, alcance, notas de la visita)",
        validators=[DataRequired(message="Captura al menos lo que el cliente indicó — es el punto de partida de todo lo demás.")],
    )
    fecha_visita = DateField("Fecha de la visita/levantamiento", validators=[Optional()])


class CotizacionItemForm(FlaskForm):
    class Meta:
        csrf = False

    concepto = StringField("Concepto", validators=[DataRequired(), Length(max=200)])
    unidad = StringField("Unidad", validators=[DataRequired(), Length(max=20)], default="pza")
    cantidad = DecimalField("Cantidad", validators=[DataRequired(), NumberRange(min=0.01)], default=1)
    precio_unitario = DecimalField("Precio unitario", validators=[DataRequired(), NumberRange(min=0.01)])


class CotizacionForm(FlaskForm):
    titulo = StringField("Título de la cotización", validators=[DataRequired(), Length(max=150)])
    notas = TextAreaField("Notas", validators=[Optional()])
    items = FieldList(FormField(CotizacionItemForm), min_entries=1)


class RechazoCotizacionForm(FlaskForm):
    motivo_rechazo = TextAreaField("Motivo del rechazo", validators=[DataRequired()])


class AceptarCotizacionForm(FlaskForm):
    responsable_id = SelectField("Responsable de la obra", coerce=int, validators=[Optional()])
    fecha_inicio = DateField("Fecha de inicio", validators=[Optional()])
    fecha_fin_estimada = DateField("Fecha fin estimada", validators=[Optional()])


class GastoForm(FlaskForm):
    categoria = SelectField("Categoría", choices=[
        ("materiales", "Materiales"), ("equipo", "Equipo"),
        ("subcontratista", "Subcontratista"), ("administrativo", "Administrativo"), ("otro", "Otro"),
    ])
    concepto = StringField("Concepto / material", validators=[DataRequired(), Length(max=200)])
    cantidad = DecimalField("Cantidad", validators=[Optional()])
    unidad = StringField("Unidad", validators=[Optional(), Length(max=20)])
    monto = DecimalField("Monto ($)", validators=[DataRequired(), NumberRange(min=0.01)])
    fecha = DateField("Fecha", validators=[DataRequired()])
    proveedor_id = SelectField("Proveedor", coerce=int, validators=[Optional()])


class TrabajadorForm(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    oficio = SelectField("Oficio", choices=[
        ("albanil", "Albañil"), ("pintor", "Pintor"), ("electricista", "Electricista"),
        ("plomero", "Plomero"), ("carpintero", "Carpintero"),
        ("ayudante_general", "Ayudante general"), ("otro", "Otro"),
    ])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=20)])
    tipo_pago = SelectField("Tipo de pago", choices=[
        ("por_dia", "Por día"), ("destajo", "Por destajo"), ("semana", "Por semana"),
    ])


class PagoManoObraForm(FlaskForm):
    trabajador_id = SelectField("Trabajador", coerce=int, validators=[DataRequired()])
    concepto = StringField("Concepto (ej. 'semana 1-8 feb, cimentación')", validators=[DataRequired(), Length(max=200)])
    dias_o_unidades = DecimalField("Días / unidades", validators=[Optional()])
    monto = DecimalField("Monto pagado ($)", validators=[DataRequired(), NumberRange(min=0.01)])
    fecha = DateField("Fecha", validators=[DataRequired()])


class AvanceForm(FlaskForm):
    semana = DateField("Semana (lunes)", validators=[DataRequired()])
    etapa = StringField("Etapa (ej. Cimentación)", validators=[DataRequired(), Length(max=100)])
    porcentaje = IntegerField("% de avance acumulado", validators=[DataRequired(), NumberRange(min=0, max=100)])
    descripcion = TextAreaField("Descripción", validators=[Optional()])


class TareaForm(FlaskForm):
    titulo = StringField("Título de la tarea", validators=[DataRequired(), Length(max=150)])
    descripcion = TextAreaField("Descripción", validators=[Optional()])
    responsable_id = SelectField("Responsable", coerce=int, validators=[Optional()])
    fecha_inicio = DateField("Fecha inicio", validators=[Optional()])
    fecha_fin = DateField("Fecha límite", validators=[Optional()])
    prioridad = SelectField("Prioridad", choices=[("baja", "Baja"), ("media", "Media"), ("alta", "Alta")])


class BitacoraForm(FlaskForm):
    fecha = DateField("Fecha", validators=[DataRequired()])
    clima = SelectField("Clima", choices=[
        ("soleado", "☀️ Soleado"), ("nublado", "☁️ Nublado"), ("lluvioso", "🌧️ Lluvioso"),
        ("frio", "🥶 Frío"), ("caluroso", "🥵 Caluroso"),
    ])
    personal_en_obra = IntegerField("Personal en obra", validators=[Optional(), NumberRange(min=0)])
    actividades = TextAreaField("Actividades realizadas", validators=[DataRequired()])
    incidencias = TextAreaField("Incidencias (opcional)", validators=[Optional()])
    fotos = MultipleFileField("Fotos del día (opcional)", validators=[
        Optional(), FileAllowed(EXTENSIONES_FOTO, "Solo imágenes (png/jpg/webp)."),
    ])


class DocumentoForm(FlaskForm):
    nombre = StringField("Nombre del documento", validators=[DataRequired(), Length(max=200)])
    categoria = SelectField("Categoría", choices=[
        ("plano", "Plano"), ("licencia", "Licencia"), ("contrato", "Contrato"),
        ("acta", "Acta"), ("factura", "Factura"), ("otro", "Otro"),
    ])
    archivo = FileField("Subir archivo", validators=[
        Optional(), FileAllowed(EXTENSIONES_DOCUMENTO, "Tipo de archivo no permitido."),
    ])
    url_archivo = StringField(
        "…o URL/ruta externa (si no subes un archivo)", validators=[Optional(), Length(max=500)],
    )
    fecha_vencimiento = DateField(
        "Fecha de vencimiento (opcional — licencias, pólizas, permisos)", validators=[Optional()],
    )
    visible_cliente = BooleanField("Visible en el portal del cliente")


class PagoClienteForm(FlaskForm):
    concepto = StringField("Concepto", validators=[DataRequired(), Length(max=150)])
    monto = DecimalField("Monto ($)", validators=[DataRequired(), NumberRange(min=0.01)])
    fecha_programada = DateField("Fecha programada", validators=[DataRequired()])


class ConceptoCatalogoForm(FlaskForm):
    concepto = StringField("Concepto", validators=[DataRequired(), Length(max=200)])
    unidad = StringField("Unidad", validators=[DataRequired(), Length(max=20)], default="pza")
    precio_unitario = DecimalField("Precio unitario", validators=[DataRequired(), NumberRange(min=0.01)])
    categoria = StringField("Categoría (opcional, ej. 'Cimentación')", validators=[Optional(), Length(max=80)])


class PortalRechazoCotizacionForm(FlaskForm):
    motivo_rechazo = TextAreaField("Motivo del rechazo", validators=[DataRequired()])


# ─────────────────────────── Inventario y compras ─────────────────────────

class MovimientoInventarioForm(FlaskForm):
    tipo = SelectField("Tipo", choices=[("entrada", "Entrada (compra/recepción)"), ("salida", "Salida (consumo)")])
    material = StringField("Material", validators=[DataRequired(), Length(max=150)])
    unidad = StringField("Unidad", validators=[DataRequired(), Length(max=20)], default="pza")
    cantidad = DecimalField("Cantidad", validators=[DataRequired(), NumberRange(min=0.01)])
    motivo = StringField("Motivo (opcional)", validators=[Optional(), Length(max=200)])
    fecha = DateField("Fecha", validators=[DataRequired()])


class OrdenCompraForm(FlaskForm):
    proveedor_id = SelectField("Proveedor", coerce=int, validators=[Optional()])
    concepto = StringField("Concepto", validators=[DataRequired(), Length(max=200)])
    cantidad = DecimalField("Cantidad", validators=[DataRequired(), NumberRange(min=0.01)], default=1)
    unidad = StringField("Unidad", validators=[DataRequired(), Length(max=20)], default="pza")
    costo_estimado = DecimalField("Costo estimado ($)", validators=[DataRequired(), NumberRange(min=0.01)])
    fecha_solicitud = DateField("Fecha de solicitud", validators=[DataRequired()])


# ─────────────────────────── Equipo y subcontratistas ──────────────────────

class EquipoForm(FlaskForm):
    nombre = StringField("Nombre del equipo", validators=[DataRequired(), Length(max=150)])
    tipo = StringField("Tipo (ej. 'Grúa torre')", validators=[Optional(), Length(max=80)])
    propio = BooleanField("Es propio (no rentado)", default=True)
    costo_renta_diario = DecimalField("Costo de renta diario ($, si aplica)", validators=[Optional()])


class AsignacionEquipoForm(FlaskForm):
    equipo_id = SelectField("Equipo", coerce=int, validators=[DataRequired()])
    fecha_inicio = DateField("Fecha de inicio", validators=[DataRequired()])
    notas = StringField("Notas (opcional)", validators=[Optional(), Length(max=200)])


class SubcontratistaForm(FlaskForm):
    nombre = StringField("Nombre / razón social", validators=[DataRequired(), Length(max=150)])
    especialidad = StringField("Especialidad (ej. 'Instalaciones eléctricas')", validators=[Optional(), Length(max=100)])
    contacto = StringField("Contacto", validators=[Optional(), Length(max=100)])
    telefono = StringField("Teléfono", validators=[Optional(), Length(max=20)])


class ContratoSubcontratistaForm(FlaskForm):
    subcontratista_id = SelectField("Subcontratista", coerce=int, validators=[DataRequired()])
    concepto = StringField("Concepto del contrato", validators=[DataRequired(), Length(max=200)])
    monto = DecimalField("Monto ($)", validators=[DataRequired(), NumberRange(min=0.01)])
    fecha_inicio = DateField("Fecha de inicio", validators=[Optional()])
    fecha_fin = DateField("Fecha fin estimada", validators=[Optional()])


# ─────────────────────────── Cambios y seguridad ───────────────────────────

class OrdenCambioForm(FlaskForm):
    descripcion = TextAreaField("Descripción del cambio pedido por el cliente", validators=[DataRequired()])
    monto = DecimalField("Monto adicional ($, puede ser negativo si reduce alcance)", validators=[DataRequired()])


class IncidenteSeguridadForm(FlaskForm):
    fecha = DateField("Fecha", validators=[DataRequired()])
    tipo = SelectField("Tipo", choices=[
        ("checklist_epp", "Checklist de EPP"), ("incidente", "Incidente"), ("casi_accidente", "Casi accidente"),
    ])
    gravedad = SelectField("Gravedad", choices=[("baja", "Baja"), ("media", "Media"), ("alta", "Alta")])
    descripcion = TextAreaField("Descripción", validators=[DataRequired()])
    accion_tomada = TextAreaField("Acción tomada (opcional)", validators=[Optional()])


# ─────────────────────────── Trabajadores: expediente y ausencias ─────────

class DocumentoTrabajadorForm(FlaskForm):
    nombre = StringField("Nombre del documento", validators=[DataRequired(), Length(max=200)])
    categoria = SelectField("Categoría", choices=[
        ("identificacion", "Identificación"), ("contrato", "Contrato"),
        ("examen_medico", "Examen médico"), ("seguro", "Seguro"), ("otro", "Otro"),
    ])
    archivo = FileField("Archivo", validators=[
        DataRequired(), FileAllowed(EXTENSIONES_DOCUMENTO, "Tipo de archivo no permitido."),
    ])
    fecha_vencimiento = DateField("Fecha de vencimiento (opcional)", validators=[Optional()])


class AusenciaTrabajadorForm(FlaskForm):
    tipo = SelectField("Tipo", choices=[
        ("vacaciones", "Vacaciones"), ("incapacidad", "Incapacidad"), ("permiso", "Permiso"),
    ])
    fecha_inicio = DateField("Fecha de inicio", validators=[DataRequired()])
    fecha_fin = DateField("Fecha de fin", validators=[DataRequired()])
    motivo = StringField("Motivo (opcional)", validators=[Optional(), Length(max=200)])


# ─────────────────────────── Plantillas de cotizacion ──────────────────────

class PlantillaCotizacionForm(FlaskForm):
    nombre = StringField("Nombre de la plantilla", validators=[DataRequired(), Length(max=150)])
    tipo_obra = SelectField("Tipo de obra", choices=[
        ("residencial", "Residencial"), ("comercial", "Comercial"),
        ("publica", "Pública"), ("mixta", "Mixta"), ("otro", "Otro"),
    ])
    items = FieldList(FormField(CotizacionItemForm), min_entries=1)


# ─────────────────────────── Mensajeria y documentos con vencimiento ──────

class MensajeObraForm(FlaskForm):
    texto = TextAreaField("Mensaje", validators=[DataRequired(), Length(max=2000)])
