from datetime import datetime, date
from flask_login import UserMixin
from .extensions import db, bcrypt


# ─────────────────────────────────────────────────────────────
# Usuarios internos y clientes
# ─────────────────────────────────────────────────────────────

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum("admin", "supervisor", "empleado", name="rol_usuario"), nullable=False, default="empleado")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    tipo = "usuario"

    def get_id(self):
        return f"usuario:{self.id}"

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def es_admin(self):
        return self.rol == "admin"

    def puede_gestionar_obras(self):
        return self.rol in ("admin", "supervisor")


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    rfc = db.Column(db.String(20))
    tipo = db.Column(db.Enum("persona_fisica", "empresa", name="tipo_cliente"), nullable=False, default="persona_fisica")
    direccion = db.Column(db.Text)
    notas = db.Column(db.Text)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    levantamientos = db.relationship("Levantamiento", back_populates="cliente", order_by="Levantamiento.creado_en.desc()")
    obras = db.relationship("Obra", back_populates="cliente")
    acceso = db.relationship("ClienteAcceso", back_populates="cliente", uselist=False)


class ClienteAcceso(UserMixin, db.Model):
    """Login independiente del portal de solo lectura para el cliente final."""
    __tablename__ = "clientes_acceso"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="acceso")

    tipo = "cliente"

    def get_id(self):
        return f"cliente:{self.id}"

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


# ─────────────────────────────────────────────────────────────
# El flujo comercial: levantamiento -> cotizacion -> obra
# ─────────────────────────────────────────────────────────────

class Levantamiento(db.Model):
    """Lo que el cliente pidio: indicaciones, notas de la visita, alcance inicial."""
    __tablename__ = "levantamientos"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    tipo_obra = db.Column(db.Enum("residencial", "comercial", "publica", "mixta", "otro", name="tipo_obra"), nullable=False)
    direccion = db.Column(db.Text)
    indicaciones_cliente = db.Column(db.Text, nullable=False)
    fecha_visita = db.Column(db.Date)
    estado = db.Column(
        db.Enum("nuevo", "en_cotizacion", "cotizado", "descartado", name="estado_levantamiento"),
        nullable=False, default="nuevo",
    )
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="levantamientos")
    creador = db.relationship("Usuario")
    cotizaciones = db.relationship(
        "Cotizacion", back_populates="levantamiento", order_by="Cotizacion.version.desc()"
    )

    @property
    def siguiente_version(self):
        return (max((c.version for c in self.cotizaciones), default=0)) + 1


class Cotizacion(db.Model):
    """Una version de cotizacion para un levantamiento. Puede haber varias (v1, v2...)."""
    __tablename__ = "cotizaciones"

    id = db.Column(db.Integer, primary_key=True)
    levantamiento_id = db.Column(db.Integer, db.ForeignKey("levantamientos.id"), nullable=False)
    version = db.Column(db.Integer, nullable=False, default=1)
    titulo = db.Column(db.String(150), nullable=False)
    notas = db.Column(db.Text)
    estado = db.Column(
        db.Enum("borrador", "enviada", "aceptada", "rechazada", name="estado_cotizacion"),
        nullable=False, default="borrador",
    )
    motivo_rechazo = db.Column(db.Text)
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    respondida_en = db.Column(db.DateTime)

    levantamiento = db.relationship("Levantamiento", back_populates="cotizaciones")
    creador = db.relationship("Usuario")
    items = db.relationship(
        "CotizacionItem", back_populates="cotizacion",
        cascade="all, delete-orphan", order_by="CotizacionItem.id",
    )
    obra = db.relationship("Obra", back_populates="cotizacion", uselist=False)

    @property
    def total(self):
        return sum((item.subtotal for item in self.items), start=0)


class CotizacionItem(db.Model):
    __tablename__ = "cotizacion_items"

    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"), nullable=False)
    concepto = db.Column(db.String(200), nullable=False)
    unidad = db.Column(db.String(20), nullable=False, default="pza")
    cantidad = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    cotizacion = db.relationship("Cotizacion", back_populates="items")

    @property
    def subtotal(self):
        return (self.cantidad or 0) * (self.precio_unitario or 0)


# ─────────────────────────────────────────────────────────────
# La obra y todo lo que ocurre dentro de ella
# ─────────────────────────────────────────────────────────────

class Obra(db.Model):
    __tablename__ = "obras"

    id = db.Column(db.Integer, primary_key=True)
    cotizacion_id = db.Column(db.Integer, db.ForeignKey("cotizaciones.id"), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.Enum("residencial", "comercial", "publica", "mixta", "otro", name="tipo_obra_ejec"), nullable=False)
    monto_contrato = db.Column(db.Numeric(14, 2), nullable=False)
    responsable_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_inicio = db.Column(db.Date)
    fecha_fin_estimada = db.Column(db.Date)
    fecha_fin_real = db.Column(db.Date)
    estado = db.Column(
        db.Enum("activa", "pausada", "terminada", "cancelada", name="estado_obra"),
        nullable=False, default="activa",
    )
    avance_porcentaje = db.Column(db.Integer, nullable=False, default=0)
    direccion = db.Column(db.Text)
    descripcion = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    cotizacion = db.relationship("Cotizacion", back_populates="obra")
    cliente = db.relationship("Cliente", back_populates="obras")
    responsable = db.relationship("Usuario")

    gastos = db.relationship("Gasto", back_populates="obra", order_by="Gasto.fecha.desc()")
    pagos_mano_obra = db.relationship("PagoManoObra", back_populates="obra", order_by="PagoManoObra.fecha.desc()")
    avances = db.relationship("AvanceObra", back_populates="obra", order_by="AvanceObra.semana.desc()")
    tareas = db.relationship("Tarea", back_populates="obra")
    bitacora = db.relationship("BitacoraObra", back_populates="obra", order_by="BitacoraObra.fecha.desc()")
    documentos = db.relationship("Documento", back_populates="obra")
    pagos_cliente = db.relationship("PagoCliente", back_populates="obra", order_by="PagoCliente.fecha_programada")

    @property
    def gasto_materiales_y_otros(self):
        return sum((g.monto for g in self.gastos), start=0)

    @property
    def gasto_mano_obra(self):
        return sum((p.monto for p in self.pagos_mano_obra), start=0)

    @property
    def gasto_real(self):
        return self.gasto_materiales_y_otros + self.gasto_mano_obra

    @property
    def saldo_presupuesto(self):
        return (self.monto_contrato or 0) - self.gasto_real

    @property
    def pct_gasto(self):
        if not self.monto_contrato:
            return 0
        return round(float(self.gasto_real) / float(self.monto_contrato) * 100)


class Proveedor(db.Model):
    __tablename__ = "proveedores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    categoria = db.Column(db.Enum("materiales", "equipo", "servicios", "otro", name="categoria_proveedor"), nullable=False, default="materiales")
    activo = db.Column(db.Boolean, nullable=False, default=True)


class Gasto(db.Model):
    """Gastos de materiales, equipo, subcontratistas y administrativos. La mano de
    obra directa (albaniles, pintores, etc.) tiene su propio modelo: PagoManoObra."""
    __tablename__ = "gastos"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    categoria = db.Column(
        db.Enum("materiales", "equipo", "subcontratista", "administrativo", "otro", name="categoria_gasto"),
        nullable=False,
    )
    concepto = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2))
    unidad = db.Column(db.String(20))
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"))
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="gastos")
    proveedor = db.relationship("Proveedor")
    registrador = db.relationship("Usuario")


class Trabajador(db.Model):
    """Personal de campo pagado por oficio: albanil, pintor, electricista, etc."""
    __tablename__ = "trabajadores"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    oficio = db.Column(
        db.Enum("albanil", "pintor", "electricista", "plomero", "carpintero", "ayudante_general", "otro", name="oficio_trabajador"),
        nullable=False,
    )
    telefono = db.Column(db.String(20))
    tipo_pago = db.Column(db.Enum("por_dia", "destajo", "semana", name="tipo_pago_trabajador"), nullable=False, default="por_dia")
    activo = db.Column(db.Boolean, nullable=False, default=True)


class PagoManoObra(db.Model):
    __tablename__ = "pagos_mano_obra"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("trabajadores.id"), nullable=False)
    concepto = db.Column(db.String(200), nullable=False)
    dias_o_unidades = db.Column(db.Numeric(6, 2))
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="pagos_mano_obra")
    trabajador = db.relationship("Trabajador")
    registrador = db.relationship("Usuario")


class AvanceObra(db.Model):
    __tablename__ = "avance_obra"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    semana = db.Column(db.Date, nullable=False)
    etapa = db.Column(db.String(100), nullable=False)
    porcentaje = db.Column(db.Integer, nullable=False)
    descripcion = db.Column(db.Text)
    reportado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="avances")
    reportador = db.relationship("Usuario")


class Tarea(db.Model):
    __tablename__ = "tareas"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    responsable_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.Enum("pendiente", "en_curso", "terminada", name="estado_tarea"), nullable=False, default="pendiente")
    prioridad = db.Column(db.Enum("baja", "media", "alta", name="prioridad_tarea"), nullable=False, default="media")
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    obra = db.relationship("Obra", back_populates="tareas")
    responsable = db.relationship("Usuario", foreign_keys=[responsable_id])


class BitacoraObra(db.Model):
    __tablename__ = "bitacora"
    __table_args__ = (db.UniqueConstraint("obra_id", "fecha", name="uq_bitacora_obra_fecha"),)

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    clima = db.Column(db.Enum("soleado", "nublado", "lluvioso", "frio", "caluroso", name="clima_bitacora"), nullable=False, default="soleado")
    personal_en_obra = db.Column(db.Integer, default=0)
    actividades = db.Column(db.Text, nullable=False)
    incidencias = db.Column(db.Text)
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="bitacora")


class Documento(db.Model):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.Enum("plano", "licencia", "contrato", "acta", "factura", "otro", name="categoria_documento"), nullable=False)
    url_archivo = db.Column(db.String(500), nullable=False)
    visible_cliente = db.Column(db.Boolean, nullable=False, default=False)
    subido_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="documentos")


class PagoCliente(db.Model):
    __tablename__ = "pagos_cliente"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    concepto = db.Column(db.String(150), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    fecha_programada = db.Column(db.Date, nullable=False)
    fecha_recibido = db.Column(db.Date)
    estado = db.Column(db.Enum("pendiente", "recibido", "vencido", "cancelado", name="estado_pago_cliente"), nullable=False, default="pendiente")

    obra = db.relationship("Obra", back_populates="pagos_cliente")
