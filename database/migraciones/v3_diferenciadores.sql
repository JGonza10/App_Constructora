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
-- DATOS DE EJEMPLO (escenario: 2026-08-21)
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
(1, 'Planos arquitectónicos v1', 'plano', '/docs/obra1/planos_v1.pdf', TRUE, 1),
(1, 'Licencia de construcción', 'licencia', '/docs/obra1/licencia.pdf', TRUE, 1),
(1, 'Contrato de obra firmado', 'contrato', '/docs/obra1/contrato.pdf', FALSE, 1),
(2, 'Planos estructurales', 'plano', '/docs/obra2/estructurales.pdf', TRUE, 1);

-- ------------------------------------------------------------
-- ACCESOS DE EJEMPLO AL PORTAL DEL CLIENTE
-- Un acceso por cliente, para validar en la prueba de rol que
-- el cliente 1 nunca puede ver datos del cliente 2 (aislamiento
-- por cliente_id, ver backend/routes/portal.js).
--
--   delgado.rios@example.com -> Cliente#2026   (Familia Delgado Ríos, obra 1)
--   contacto@altavista.mx    -> Altavista#2026 (Grupo Constructor Altavista, obra 2)
--
-- Contraseñas en claro documentadas solo aquí y en
-- INFORME_ANALISIS_Y_MANUAL_USUARIO.md para
-- pruebas; en la tabla siempre quedan hasheadas con bcrypt. En un alta real
-- de cliente, genera el hash con database/generar_acceso_cliente.py y
-- entrega la contraseña temporal al cliente por un canal fuera de banda
-- (no por correo/WhatsApp en texto plano) exigiendo cambio en el primer login.
-- ------------------------------------------------------------
INSERT INTO clientes_acceso (cliente_id, email, password) VALUES
(1, 'delgado.rios@example.com', '$2b$10$KMAeD/vhYvsUmTjkBEUZgu6jUtIP1HyNxjAI/svljOR2yalbJd9XO'),
(2, 'contacto@altavista.mx',    '$2b$10$e6lmne0NkRS/.gdNFWnmUOnB1cGRIe/q5r3Bk1y2hBCbBh/kU.KpG');
