-- ============================================
-- BASE DE DATOS: Sistema Constructora
-- Roles: admin, supervisor, empleado
-- ============================================

CREATE DATABASE IF NOT EXISTS constructora;
USE constructora;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  rol ENUM('admin', 'supervisor', 'empleado') DEFAULT 'empleado',
  activo BOOLEAN DEFAULT TRUE,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de presupuestos
CREATE TABLE IF NOT EXISTS presupuestos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  titulo VARCHAR(150) NOT NULL,
  descripcion TEXT,
  monto DECIMAL(12, 2) NOT NULL,
  estado ENUM('borrador', 'revision', 'aprobado', 'rechazado') DEFAULT 'borrador',
  creado_por INT NOT NULL,
  revisado_por INT,
  comentario_revision TEXT,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (creado_por) REFERENCES usuarios(id),
  FOREIGN KEY (revisado_por) REFERENCES usuarios(id)
);

-- Tabla de alertas (para Socket.io)
CREATE TABLE IF NOT EXISTS alertas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  mensaje TEXT NOT NULL,
  tipo ENUM('info', 'warning', 'success', 'error') DEFAULT 'info',
  usuario_id INT,
  leida BOOLEAN DEFAULT FALSE,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ============================================
-- DATOS DE EJEMPLO (escenario: 2026-08-21)
-- Cuentas de prueba para validar cada rol interno.
-- Contraseñas en claro SOLO documentadas aquí y en
-- INFORME_ANALISIS_Y_MANUAL_USUARIO.md para fines de prueba; en la
-- base de datos siempre viven hasheadas
-- con bcrypt (nunca en texto plano). Cámbialas antes de producción.
--
--   ana.ramirez@constructora.com      -> Ana Ramírez      (admin)      -> Direccion#2026
--   jorge.villasenor@constructora.com -> Jorge Villaseñor  (supervisor) -> Supervisa#2026
--   paola.reyes@constructora.com      -> Paola Reyes       (empleado)   -> Campo#2026
--
-- (regenerados con: node -e "require('bcrypt').hashSync(pwd,10)")
-- ============================================
INSERT INTO usuarios (nombre, email, password, rol) VALUES
  ('Ana Ramírez',      'ana.ramirez@constructora.com',      '$2b$10$2pAlZ0Uylx0dMtdswKmTJeA1aXfDN/8u3GixkuthTNZZfNU48lvGO', 'admin'),
  ('Jorge Villaseñor', 'jorge.villasenor@constructora.com',  '$2b$10$NoDefJD4L6lNu.4l6QyQkeEHhsZCQsKD3Ug82jAiRVXL3Hgeh7wQi', 'supervisor'),
  ('Paola Reyes',      'paola.reyes@constructora.com',       '$2b$10$aRDC.oXoiOfbgMJMdeJ9yeFbcFK6aydPkv.UF1aIVwMTKgsRBtXAK', 'empleado');

-- Los presupuestos de ejemplo se insertan en migraciones/v2_ampliacion.sql,
-- después de que la columna obra_id existe, para que queden ligados a una obra real.

INSERT INTO alertas (mensaje, tipo, usuario_id) VALUES
('Bienvenida: cuenta de administrador lista para el recorrido de prueba', 'info', 1),
('Recuerda: hay un presupuesto pendiente de revisión en la Torre Altavista', 'warning', 2);
