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
    firma_url = db.Column(db.String(300))
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
    nivel_alerta_presupuesto = db.Column(db.Integer, nullable=False, default=0)
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
    movimientos_inventario = db.relationship("MovimientoInventario", back_populates="obra", order_by="MovimientoInventario.fecha.desc()")
    ordenes_compra = db.relationship("OrdenCompra", back_populates="obra", order_by="OrdenCompra.creado_en.desc()")
    asistencias = db.relationship("Asistencia", back_populates="obra")
    ordenes_cambio = db.relationship("OrdenCambio", back_populates="obra", order_by="OrdenCambio.creado_en.desc()")
    incidentes_seguridad = db.relationship("IncidenteSeguridad", back_populates="obra", order_by="IncidenteSeguridad.fecha.desc()")
    asignaciones_equipo = db.relationship("AsignacionEquipo", back_populates="obra")
    contratos_subcontratista = db.relationship("ContratoSubcontratista", back_populates="obra")
    mensajes = db.relationship("MensajeObra", back_populates="obra", order_by="MensajeObra.creado_en")

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

    def inventario_resumen(self):
        """Existencia actual por material: suma de entradas menos salidas.
        No se guarda un saldo aparte a proposito — se recalcula del historial
        de movimientos, igual que gasto_real se recalcula de Gasto."""
        saldos = {}
        for m in self.movimientos_inventario:
            clave = (m.material, m.unidad)
            signo = 1 if m.tipo == "entrada" else -1
            saldos[clave] = saldos.get(clave, 0) + signo * float(m.cantidad)
        return {f"{material} ({unidad})": cantidad for (material, unidad), cantidad in saldos.items()}


class ConceptoCatalogo(db.Model):
    """Banco de conceptos/precios unitarios reutilizables al armar una cotizacion,
    para no volver a teclear el mismo concepto y precio cada vez."""
    __tablename__ = "catalogo_conceptos"

    id = db.Column(db.Integer, primary_key=True)
    concepto = db.Column(db.String(200), nullable=False)
    unidad = db.Column(db.String(20), nullable=False, default="pza")
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)
    categoria = db.Column(db.String(80))
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


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

    documentos = db.relationship("DocumentoTrabajador", back_populates="trabajador", cascade="all, delete-orphan")
    ausencias = db.relationship("AusenciaTrabajador", back_populates="trabajador", order_by="AusenciaTrabajador.fecha_inicio.desc()")


class DocumentoTrabajador(db.Model):
    """Expediente digital: identificacion, contrato, vigencias (examen medico,
    seguro). Mismo mecanismo de archivo que Documento/BitacoraFoto."""
    __tablename__ = "documentos_trabajador"

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("trabajadores.id"), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(
        db.Enum("identificacion", "contrato", "examen_medico", "seguro", "otro", name="categoria_documento_trabajador"),
        nullable=False,
    )
    ruta_archivo = db.Column(db.String(300), nullable=False)
    fecha_vencimiento = db.Column(db.Date)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    trabajador = db.relationship("Trabajador", back_populates="documentos")


class AusenciaTrabajador(db.Model):
    __tablename__ = "ausencias_trabajador"

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("trabajadores.id"), nullable=False)
    tipo = db.Column(db.Enum("vacaciones", "incapacidad", "permiso", name="tipo_ausencia"), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(200))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    trabajador = db.relationship("Trabajador", back_populates="ausencias")

    def incluye(self, fecha):
        return self.fecha_inicio <= fecha <= self.fecha_fin


class Asistencia(db.Model):
    """Independiente de PagoManoObra: quien llego cada dia, base para armar
    la nomina en vez de tecleria a mano al pagar."""
    __tablename__ = "asistencias"
    __table_args__ = (db.UniqueConstraint("trabajador_id", "fecha", name="uq_asistencia_trabajador_fecha"),)

    id = db.Column(db.Integer, primary_key=True)
    trabajador_id = db.Column(db.Integer, db.ForeignKey("trabajadores.id"), nullable=False)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    presente = db.Column(db.Boolean, nullable=False, default=True)
    notas = db.Column(db.String(200))
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    trabajador = db.relationship("Trabajador")
    obra = db.relationship("Obra", back_populates="asistencias")


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
    fotos = db.relationship("BitacoraFoto", back_populates="bitacora", cascade="all, delete-orphan")


class BitacoraFoto(db.Model):
    """Evidencia fotografica de un registro de bitacora. Tabla propia (no una
    columna en BitacoraObra) porque un dia puede traer varias fotos."""
    __tablename__ = "bitacora_fotos"

    id = db.Column(db.Integer, primary_key=True)
    bitacora_id = db.Column(db.Integer, db.ForeignKey("bitacora.id"), nullable=False)
    ruta_archivo = db.Column(db.String(300), nullable=False)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    bitacora = db.relationship("BitacoraObra", back_populates="fotos")


class Documento(db.Model):
    __tablename__ = "documentos"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    nombre = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.Enum("plano", "licencia", "contrato", "acta", "factura", "otro", name="categoria_documento"), nullable=False)
    url_archivo = db.Column(db.String(500), nullable=False)
    visible_cliente = db.Column(db.Boolean, nullable=False, default=False)
    fecha_vencimiento = db.Column(db.Date)
    aviso_vencimiento_enviado = db.Column(db.Boolean, nullable=False, default=False)
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


# ─────────────────────────────────────────────────────────────
# Inventario y compras
# ─────────────────────────────────────────────────────────────

class MovimientoInventario(db.Model):
    """Entradas y salidas de material por obra. No hay tabla de 'saldo' aparte
    a proposito — Obra.inventario_resumen() lo recalcula del historial, igual
    que gasto_real se recalcula de Gasto en vez de guardarse aparte."""
    __tablename__ = "movimientos_inventario"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    tipo = db.Column(db.Enum("entrada", "salida", name="tipo_movimiento_inventario"), nullable=False)
    material = db.Column(db.String(150), nullable=False)
    unidad = db.Column(db.String(20), nullable=False, default="pza")
    cantidad = db.Column(db.Numeric(10, 2), nullable=False)
    motivo = db.Column(db.String(200))
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="movimientos_inventario")


class OrdenCompra(db.Model):
    """Un pedido a proveedor ANTES de que se pague — distinto de Gasto, que ya
    es un hecho consumado. Al marcarse 'recibida' se puede generar el Gasto y
    la entrada de inventario correspondientes (ver obras.recibir_orden_compra)."""
    __tablename__ = "ordenes_compra"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"))
    concepto = db.Column(db.String(200), nullable=False)
    cantidad = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    unidad = db.Column(db.String(20), nullable=False, default="pza")
    costo_estimado = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(
        db.Enum("solicitada", "confirmada", "recibida", "cancelada", name="estado_orden_compra"),
        nullable=False, default="solicitada",
    )
    fecha_solicitud = db.Column(db.Date, nullable=False, default=date.today)
    fecha_recibido = db.Column(db.Date)
    gasto_generado_id = db.Column(db.Integer, db.ForeignKey("gastos.id"))
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="ordenes_compra")
    proveedor = db.relationship("Proveedor")
    gasto_generado = db.relationship("Gasto")


# ─────────────────────────────────────────────────────────────
# Equipo y maquinaria
# ─────────────────────────────────────────────────────────────

class Equipo(db.Model):
    __tablename__ = "equipo"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(80))
    propio = db.Column(db.Boolean, nullable=False, default=True)
    costo_renta_diario = db.Column(db.Numeric(10, 2))
    activo = db.Column(db.Boolean, nullable=False, default=True)


class AsignacionEquipo(db.Model):
    __tablename__ = "asignaciones_equipo"

    id = db.Column(db.Integer, primary_key=True)
    equipo_id = db.Column(db.Integer, db.ForeignKey("equipo.id"), nullable=False)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False, default=date.today)
    fecha_fin = db.Column(db.Date)
    notas = db.Column(db.String(200))

    equipo = db.relationship("Equipo")
    obra = db.relationship("Obra", back_populates="asignaciones_equipo")

    @property
    def activa(self):
        return self.fecha_fin is None


# ─────────────────────────────────────────────────────────────
# Cambios de alcance y seguridad
# ─────────────────────────────────────────────────────────────

class OrdenCambio(db.Model):
    """Cuando el cliente pide algo extra a media obra: sube Obra.monto_contrato
    de forma trazable y con aprobacion, en vez de editar el campo a mano."""
    __tablename__ = "ordenes_cambio"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(db.Enum("pendiente", "aprobada", "rechazada", name="estado_orden_cambio"), nullable=False, default="pendiente")
    creado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resuelta_en = db.Column(db.DateTime)

    obra = db.relationship("Obra", back_populates="ordenes_cambio")


class IncidenteSeguridad(db.Model):
    """Distinto de BitacoraObra (que es actividad diaria general): checklist
    de EPP e incidentes de seguridad e higiene, obligacion propia del giro."""
    __tablename__ = "incidentes_seguridad"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    tipo = db.Column(db.Enum("checklist_epp", "incidente", "casi_accidente", name="tipo_incidente_seguridad"), nullable=False)
    gravedad = db.Column(db.Enum("baja", "media", "alta", name="gravedad_incidente"), nullable=False, default="baja")
    descripcion = db.Column(db.Text, nullable=False)
    accion_tomada = db.Column(db.Text)
    registrado_por = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="incidentes_seguridad")


# ─────────────────────────────────────────────────────────────
# Subcontratistas
# ─────────────────────────────────────────────────────────────

class Subcontratista(db.Model):
    __tablename__ = "subcontratistas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    especialidad = db.Column(db.String(100))
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    activo = db.Column(db.Boolean, nullable=False, default=True)


class ContratoSubcontratista(db.Model):
    __tablename__ = "contratos_subcontratista"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    subcontratista_id = db.Column(db.Integer, db.ForeignKey("subcontratistas.id"), nullable=False)
    concepto = db.Column(db.String(200), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    avance_porcentaje = db.Column(db.Integer, nullable=False, default=0)
    estado = db.Column(db.Enum("activo", "terminado", "cancelado", name="estado_contrato_subcontratista"), nullable=False, default="activo")
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    obra = db.relationship("Obra", back_populates="contratos_subcontratista")
    subcontratista = db.relationship("Subcontratista")


# ─────────────────────────────────────────────────────────────
# Plantillas de cotizacion
# ─────────────────────────────────────────────────────────────

class PlantillaCotizacion(db.Model):
    __tablename__ = "plantillas_cotizacion"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    tipo_obra = db.Column(db.Enum("residencial", "comercial", "publica", "mixta", "otro", name="tipo_obra_plantilla"), nullable=False)

    items = db.relationship("PlantillaItem", back_populates="plantilla", cascade="all, delete-orphan")

    @property
    def total(self):
        return sum(((item.cantidad or 0) * item.precio_unitario for item in self.items), start=0)


class PlantillaItem(db.Model):
    __tablename__ = "plantilla_items"

    id = db.Column(db.Integer, primary_key=True)
    plantilla_id = db.Column(db.Integer, db.ForeignKey("plantillas_cotizacion.id"), nullable=False)
    concepto = db.Column(db.String(200), nullable=False)
    unidad = db.Column(db.String(20), nullable=False, default="pza")
    cantidad = db.Column(db.Numeric(10, 2), nullable=False, default=1)
    precio_unitario = db.Column(db.Numeric(12, 2), nullable=False)

    plantilla = db.relationship("PlantillaCotizacion", back_populates="items")


# ─────────────────────────────────────────────────────────────
# Mensajeria y auditoria
# ─────────────────────────────────────────────────────────────

class MensajeObra(db.Model):
    """Hilo de mensajes por obra entre el equipo interno y el cliente del
    portal — 'autor_tipo' distingue de que lado vino, igual que current_user.tipo."""
    __tablename__ = "mensajes_obra"

    id = db.Column(db.Integer, primary_key=True)
    obra_id = db.Column(db.Integer, db.ForeignKey("obras.id"), nullable=False)
    autor_tipo = db.Column(db.Enum("usuario", "cliente", name="autor_tipo_mensaje"), nullable=False)
    autor_nombre = db.Column(db.String(150), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    obra = db.relationship("Obra", back_populates="mensajes")


class RegistroAuditoria(db.Model):
    """Quien cambio que — solo para acciones criticas (montos, estados de obra
    y de cotizacion), no un log general de toda la app."""
    __tablename__ = "registros_auditoria"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    usuario_nombre = db.Column(db.String(150))
    accion = db.Column(db.String(100), nullable=False)
    entidad = db.Column(db.String(50), nullable=False)
    entidad_id = db.Column(db.Integer)
    detalle = db.Column(db.Text)
    creado_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
