-- ============================================================
-- MIGRACIÓN v3: Estimación de materiales, portal cliente, documentos
-- Ejecutar DESPUÉS de v2_ampliacion.sql
-- ============================================================

USE constructora;

-- ------------------------------------------------------------
-- CATÁLOGO DE PRECIOS DE MATERIALES (actualizable)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS catalogo_materiales (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  nombre          VARCHAR(150) NOT NULL,
  unidad          VARCHAR(20) NOT NULL,        -- m3, m2, ton, pza, kg
  precio_unitario DECIMAL(10,2) NOT NULL,
  categoria       ENUM('cimentacion','estructura','albanileria','acabados','instalaciones','otro') NOT NULL,
  actualizado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- ESTIMACIONES GUARDADAS (calculadora por obra)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estimaciones (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  obra_id         INT NOT NULL,
  nombre          VARCHAR(150) NOT NULL,   -- ej. "Estimación cimentación v1"
  notas           TEXT,
  total            DECIMAL(12,2) NOT NULL DEFAULT 0,
  creado_por      INT,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)    REFERENCES obras(id),
  FOREIGN KEY (creado_por) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS estimacion_items (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  estimacion_id   INT NOT NULL,
  material_id     INT NOT NULL,
  cantidad        DECIMAL(10,2) NOT NULL,
  precio_unitario DECIMAL(10,2) NOT NULL,    -- copia del precio al momento de estimar
  subtotal        DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (estimacion_id) REFERENCES estimaciones(id) ON DELETE CASCADE,
  FOREIGN KEY (material_id)   REFERENCES catalogo_materiales(id)
);

-- ------------------------------------------------------------
-- DOCUMENTOS POR OBRA (planos, licencias, contratos, actas)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documentos (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  obra_id         INT NOT NULL,
  nombre          VARCHAR(200) NOT NULL,
  categoria       ENUM('plano','licencia','contrato','acta','factura','otro') NOT NULL,
  url_archivo     VARCHAR(500) NOT NULL,     -- ruta o URL del archivo almacenado
  version         INT DEFAULT 1,
  visible_cliente BOOLEAN DEFAULT FALSE,     -- si aparece en el portal del cliente
  subido_por      INT,
  creado_en       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (obra_id)    REFERENCES obras(id),
  FOREIGN KEY (subido_por) REFERENCES usuarios(id)
);

-- ------------------------------------------------------------
-- ACCESOS DE PORTAL PARA CLIENTES (login propio, solo lectura)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clientes_acceso (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id    INT NOT NULL UNIQUE,
  email         VARCHAR(100) UNIQUE NOT NULL,
  password      VARCHAR(255) NOT NULL,
  activo        BOOLEAN DEFAULT TRUE,
  creado_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- ------------------------------------------------------------
-- DATOS DE EJEMPLO
-- ------------------------------------------------------------
INSERT INTO catalogo_materiales (nombre, unidad, precio_unitario, categoria) VALUES
('Concreto premezclado f''c=200', 'm3', 1850.00, 'cimentacion'),
('Concreto premezclado f''c=250', 'm3', 1980.00, 'estructura'),
('Varilla 3/8"', 'ton', 17500.00, 'estructura'),
('Varilla 1/2"', 'ton', 17200.00, 'estructura'),
('Block hueco 15x20x40', 'pza', 12.50, 'albanileria'),
('Cemento gris 50kg', 'pza', 195.00, 'albanileria'),
('Arena de río', 'm3', 420.00, 'albanileria'),
('Grava 3/4"', 'm3', 480.00, 'albanileria'),
('Piso porcelanato 60x60', 'm2', 285.00, 'acabados'),
('Pintura vinílica interior', 'cubeta 19L', 980.00, 'acabados'),
('Tubería PVC hidráulica 1/2"', 'pza 6m', 95.00, 'instalaciones'),
('Cable THW calibre 12', 'm', 14.50, 'instalaciones');

INSERT INTO documentos (obra_id, nombre, categoria, url_archivo, visible_cliente, subido_por) VALUES
(1, 'Planos arquitectónicos v2', 'plano', '/docs/obra1/planos_v2.pdf', TRUE, 1),
(1, 'Licencia de construcción', 'licencia', '/docs/obra1/licencia.pdf', TRUE, 1),
(1, 'Contrato de obra', 'contrato', '/docs/obra1/contrato.pdf', FALSE, 1),
(2, 'Planos estructurales', 'plano', '/docs/obra2/estructurales.pdf', TRUE, 1);
