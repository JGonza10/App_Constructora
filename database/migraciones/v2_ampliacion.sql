-- ============================================================
-- MIGRACIÓN v2: Sistema completo para despacho de arquitectura
-- Ejecutar DESPUÉS de constructora.sql
-- VERSIÓN CORREGIDA: se separó el ALTER TABLE de presupuestos
-- en dos sentencias (ADD COLUMN y ADD CONSTRAINT por separado)
-- ============================================================

USE constructora;

-- ------------------------------------------------------------
-- CLIENTES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  nombre        VARCHAR(150) NOT NULL,
  email         VARCHAR(100),
  telefono      VARCHAR(20),
  rfc           VARCHAR(20),
  tipo          ENUM('persona_fisica','empresa') DEFAULT 'persona_fisica',
  direccion     TEXT,
  notas         TEXT,
  activo        BOOLEAN DEFAULT TRUE,
  creado_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- OBRAS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS obras (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  nombre              VARCHAR(150) NOT NULL,
  tipo                ENUM('residencial','comercial','publica','mixta','otro') NOT NULL,
  cliente_id          INT NOT NULL,
  responsable_id      INT,
  monto_contrato      DECIMAL(14,2) NOT NULL DEFAULT 0,
  fecha_inicio        DATE,
  fecha_fin_estimada  DATE,
  fecha_fin_real      DATE,
  estado              ENUM('cotizacion','activa','pausada','terminada','cancelada') DEFAULT 'cotizacion',
  avance_porcentaje   TINYINT UNSIGNED DEFAULT 0,
  direccion           TEXT,
  descripcion         TEXT,
  creado_por          INT,
  creado_en           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id)     REFERENCES clientes(id),
  FOREIGN KEY (responsable_id) REFERENCES usuarios(id),
  FOREIGN KEY (creado_por)     REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- Vincular presupuestos a obra
-- CORREGIDO: se separa en dos ALTER TABLE independientes
-- ------------------------------------------------------------

-- Paso 1: agregar la columna obra_id
ALTER TABLE presupuestos
  ADD COLUMN obra_id INT NULL AFTER id;

-- Paso 2: agregar la llave foránea (FK) apuntando a obras(id)
ALTER TABLE presupuestos
  ADD CONSTRAINT fk_presupuesto_obra
    FOREIGN KEY (obra_id) REFERENCES obras(id);

-- ------------------------------------------------------------
-- GASTOS REALES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS gastos (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  obra_id         INT NOT NULL,
  categoria       ENUM('materiales','mano_obra','subcontratista','equipo','administrativo','otro') NOT NULL,
  concepto        VARCHAR(200) NOT NULL,
  monto           DECIMAL(12,2) NOT NULL,
  fecha           DATE NOT NULL,
  proveedor_id    INT,
  comprobante     VARCHAR(255),
  notas           TEXT,
  registrado_por  INT,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)        REFERENCES obras(id),
  FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- AVANCE SEMANAL DE OBRA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS avance_obra (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  obra_id         INT NOT NULL,
  semana          DATE NOT NULL,           -- lunes de la semana
  etapa           VARCHAR(100) NOT NULL,   -- 'Cimentación', 'Estructura', etc.
  porcentaje      TINYINT UNSIGNED NOT NULL,
  descripcion     TEXT,
  foto_url        VARCHAR(500),
  reportado_por   INT,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)      REFERENCES obras(id),
  FOREIGN KEY (reportado_por) REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- PAGOS DEL CLIENTE (calendario de cobros)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pagos_cliente (
  id               INT AUTO_INCREMENT PRIMARY KEY,
  obra_id          INT NOT NULL,
  concepto         VARCHAR(150) NOT NULL,
  monto            DECIMAL(12,2) NOT NULL,
  fecha_programada DATE NOT NULL,
  fecha_recibido   DATE,
  estado           ENUM('pendiente','recibido','vencido','cancelado') DEFAULT 'pendiente',
  notas            TEXT,
  creado_en        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id) REFERENCES obras(id)
);

-- ------------------------------------------------------------
-- PROVEEDORES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS proveedores (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(150) NOT NULL,
  contacto    VARCHAR(100),
  email       VARCHAR(100),
  telefono    VARCHAR(20),
  rfc         VARCHAR(20),
  categoria   ENUM('materiales','mano_obra','equipo','servicios','otro') NOT NULL,
  notas       TEXT,
  activo      BOOLEAN DEFAULT TRUE,
  creado_en   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agregar FK de gastos a proveedores
ALTER TABLE gastos
  ADD CONSTRAINT fk_gasto_proveedor
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id);

-- ------------------------------------------------------------
-- ÓRDENES DE COMPRA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ordenes_compra (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  obra_id         INT NOT NULL,
  proveedor_id    INT NOT NULL,
  concepto        VARCHAR(200) NOT NULL,
  monto_estimado  DECIMAL(12,2),
  monto_real      DECIMAL(12,2),
  fecha_pedido    DATE NOT NULL,
  fecha_entrega   DATE,
  estado          ENUM('solicitada','confirmada','entregada','cancelada') DEFAULT 'solicitada',
  notas           TEXT,
  creado_por      INT,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)     REFERENCES obras(id),
  FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
  FOREIGN KEY (creado_por)  REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- TAREAS DE OBRA (calendario)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tareas (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  obra_id         INT NOT NULL,
  titulo          VARCHAR(150) NOT NULL,
  descripcion     TEXT,
  responsable_id  INT,
  fecha_inicio    DATE,
  fecha_fin       DATE,
  estado          ENUM('pendiente','en_curso','terminada','atrasada') DEFAULT 'pendiente',
  prioridad       ENUM('baja','media','alta') DEFAULT 'media',
  creado_por      INT,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)        REFERENCES obras(id),
  FOREIGN KEY (responsable_id) REFERENCES usuarios(id),
  FOREIGN KEY (creado_por)     REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- BITÁCORA DE OBRA
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bitacora (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  obra_id       INT NOT NULL,
  fecha         DATE NOT NULL,
  clima         ENUM('soleado','nublado','lluvioso','frio','caluroso') DEFAULT 'soleado',
  personal_qty  TINYINT UNSIGNED DEFAULT 0,
  actividades   TEXT NOT NULL,
  incidencias   TEXT,
  materiales    TEXT,
  notas         TEXT,
  registrado_por INT,
  creado_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)        REFERENCES obras(id),
  FOREIGN KEY (registrado_por) REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- DATOS DE EJEMPLO
-- ------------------------------------------------------------
INSERT INTO clientes (nombre, email, telefono, rfc, tipo) VALUES
('Familia Hernández Torres', 'hernandez@gmail.com', '5512345678', 'HETF800101AA1', 'persona_fisica'),
('Grupo Inmobiliario Nexus SA', 'contacto@nexus.com.mx', '5598765432', 'GIN901215BB2', 'empresa'),
('Ayuntamiento de Tlalpan', 'obras@tlalpan.gob.mx', '5587654321', 'ATL700610CC3', 'empresa');

INSERT INTO obras (nombre, tipo, cliente_id, responsable_id, monto_contrato, fecha_inicio, fecha_fin_estimada, estado, avance_porcentaje, creado_por) VALUES
('Casa Habitación Pedregal', 'residencial', 1, 2, 1850000.00, '2024-01-15', '2024-09-30', 'activa', 45, 1),
('Torre Corporativa Nexus', 'comercial', 2, 2, 12500000.00, '2024-03-01', '2025-06-30', 'activa', 18, 1),
('Renovación Mercado Municipal', 'publica', 3, 2, 3200000.00, '2024-02-10', '2024-12-15', 'pausada', 62, 1);

INSERT INTO pagos_cliente (obra_id, concepto, monto, fecha_programada, estado) VALUES
(1, 'Anticipo 30%', 555000.00, '2024-01-15', 'recibido'),
(1, 'Avance 50%', 370000.00, '2024-04-30', 'pendiente'),
(1, 'Finiquito 20%', 370000.00, '2024-09-30', 'pendiente'),
(2, 'Anticipo 25%', 3125000.00, '2024-03-01', 'recibido'),
(2, 'Primer estimación', 2500000.00, '2024-06-30', 'vencido');

INSERT INTO proveedores (nombre, contacto, telefono, categoria) VALUES
('CEMEX México', 'Ventas CDMX', '8008026326', 'materiales'),
('Varillas del Norte SA', 'Carlos Mendez', '5544332211', 'materiales'),
('Grúas y Equipos MX', 'Soporte', '5566778899', 'equipo');

INSERT INTO gastos (obra_id, categoria, concepto, monto, fecha, registrado_por) VALUES
(1, 'materiales', 'Concreto premezclado 30m3', 45000.00, '2024-02-01', 3),
(1, 'mano_obra', 'Cuadrilla semana 1-8 feb', 28000.00, '2024-02-08', 3),
(2, 'materiales', 'Varilla 3/8" — 5 toneladas', 87500.00, '2024-03-15', 3),
(2, 'subcontratista', 'Instalación eléctrica planta baja', 120000.00, '2024-04-01', 3);
