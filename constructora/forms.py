from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, TextAreaField, SelectField, DecimalField,
    IntegerField, DateField, BooleanField, FieldList, FormField, HiddenField,
)
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length


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


class DocumentoForm(FlaskForm):
    nombre = StringField("Nombre del documento", validators=[DataRequired(), Length(max=200)])
    categoria = SelectField("Categoría", choices=[
        ("plano", "Plano"), ("licencia", "Licencia"), ("contrato", "Contrato"),
        ("acta", "Acta"), ("factura", "Factura"), ("otro", "Otro"),
    ])
    url_archivo = StringField("URL o ruta del archivo", validators=[DataRequired(), Length(max=500)])
    visible_cliente = BooleanField("Visible en el portal del cliente")


class PagoClienteForm(FlaskForm):
    concepto = StringField("Concepto", validators=[DataRequired(), Length(max=150)])
    monto = DecimalField("Monto ($)", validators=[DataRequired(), NumberRange(min=0.01)])
    fecha_programada = DateField("Fecha programada", validators=[DataRequired()])
