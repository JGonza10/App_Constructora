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
-- DATOS DE EJEMPLO (escenario: 2026-08-21)
-- Dos clientes con una obra cada uno, para poder validar en el
-- Portal del Cliente que un cliente NUNCA ve la obra del otro.
-- ------------------------------------------------------------
INSERT INTO clientes (nombre, email, telefono, rfc, tipo) VALUES
('Familia Delgado Ríos', 'delgado.rios@example.com', '5511122233', 'DERI850312AB4', 'persona_fisica'),
('Grupo Constructor Altavista SA de CV', 'contacto@altavista.mx', '5544455566', 'GCA150822CD7', 'empresa');

INSERT INTO obras (nombre, tipo, cliente_id, responsable_id, monto_contrato, fecha_inicio, fecha_fin_estimada, estado, avance_porcentaje, creado_por) VALUES
('Residencia Delgado Ríos', 'residencial', 1, 2, 1950000.00, '2026-02-10', '2026-11-30', 'activa', 35, 1),
('Plaza Comercial Altavista', 'comercial',   2, 2, 8400000.00, '2026-03-01', '2027-05-31', 'activa', 12, 1);

-- Presupuestos ligados a obra_id (columna agregada arriba en esta misma migración)
INSERT INTO presupuestos (obra_id, titulo, descripcion, monto, estado, creado_por, revisado_por) VALUES
(1, 'Cimentación y estructura - Residencia Delgado Ríos', 'Excavación, zapatas, trabes de liga y castillos', 620000.00, 'aprobado', 3, 2),
(2, 'Instalaciones eléctricas e hidráulicas - Plaza Altavista', 'Instalación completa planta baja y primer nivel', 1450000.00, 'revision', 3, NULL),
(1, 'Acabados y pintura - Residencia Delgado Ríos', 'Pisos, pintura interior/exterior y herrería', 310000.00, 'borrador', 3, NULL);

INSERT INTO pagos_cliente (obra_id, concepto, monto, fecha_programada, fecha_recibido, estado) VALUES
(1, 'Anticipo 30%',    585000.00, '2026-02-10', '2026-02-10', 'recibido'),
(1, 'Avance 40%',      780000.00, '2026-06-30', NULL,         'pendiente'),
(1, 'Finiquito 30%',   585000.00, '2026-11-30', NULL,         'pendiente'),
(2, 'Anticipo 25%',   2100000.00, '2026-03-01', '2026-03-03', 'recibido'),
(2, 'Primera estimación', 1500000.00, '2026-06-15', NULL,     'vencido');

INSERT INTO proveedores (nombre, contacto, telefono, categoria) VALUES
('CEMEX México', 'Ventas CDMX', '8008026326', 'materiales'),
('Aceros del Bajío', 'Carlos Méndez', '5544332211', 'materiales'),
('Renta de Maquinaria GDL', 'Soporte', '5566778899', 'equipo');

INSERT INTO gastos (obra_id, categoria, concepto, monto, fecha, proveedor_id, registrado_por) VALUES
(1, 'materiales',      'Concreto premezclado 40m3', 58000.00, '2026-02-20', 1, 3),
(1, 'mano_obra',       'Cuadrilla cimentación, semana 1', 32000.00, '2026-02-27', NULL, 3),
(2, 'materiales',      'Acero de refuerzo, 8 toneladas', 142000.00, '2026-03-20', 2, 3),
(2, 'equipo',          'Renta de grúa torre - marzo', 65000.00, '2026-03-25', 3, 3);

INSERT INTO avance_obra (obra_id, semana, etapa, porcentaje, descripcion, reportado_por) VALUES
(1, '2026-02-16', 'Cimentación',  20, 'Excavación y plantilla terminadas', 3),
(1, '2026-03-02', 'Cimentación',  35, 'Colado de zapatas y trabes de liga', 3),
(2, '2026-03-09', 'Preliminares', 12, 'Trazo, nivelación y cimbra inicial', 3);

INSERT INTO tareas (obra_id, titulo, descripcion, responsable_id, fecha_inicio, fecha_fin, estado, prioridad, creado_por) VALUES
(1, 'Solicitar inspección municipal de cimentación', 'Agendar visita antes de continuar con estructura', 3, '2026-03-03', '2026-03-10', 'pendiente', 'alta', 2),
(2, 'Cotizar segunda entrega de acero', 'Comparar con Aceros del Bajío y un segundo proveedor', 3, '2026-03-15', '2026-03-28', 'en_curso', 'media', 2);

INSERT INTO bitacora (obra_id, fecha, clima, personal_qty, actividades, incidencias, registrado_por) VALUES
(1, '2026-03-02', 'soleado', 8,  'Colado de zapatas, cuadrilla completa', NULL, 3),
(2, '2026-03-09', 'nublado', 12, 'Trazo y nivelación de plataforma', 'Retraso de 2h por lluvia en la mañana', 3);
