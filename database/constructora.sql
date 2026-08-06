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
-- DATOS DE EJEMPLO
-- ============================================

-- Passwords: Admin123! / Super123! / Empl123! (bcrypt hash placeholder)
INSERT INTO usuarios (nombre, email, password, rol) VALUES
  ('Carlos Admin', 'admin@constructora.com', '$2b$10$psHpOX6OCkgVYj8uDg3KqOGy1gM0ZVJBmqwnG85dMIr9z9fhpL9Uu', 'admin'),
  ('Laura Supervisora', 'supervisor@constructora.com', '$2b$10$hzjyv/pGAkP0YUdiGwYg2eoVPKdVRtld80SgugS2YM9365Dl25h.2', 'supervisor'),
  ('Miguel Empleado', 'empleado@constructora.com', '$2b$10$JaIVx7T2lJGMviOAzuqrleU6JgH0xt.mhdK9wukfceemGzBXmc62O', 'empleado');

INSERT INTO presupuestos (titulo, descripcion, monto, estado, creado_por) VALUES
('Obra Norte - Cimientos', 'Excavación y cimientos edificio norte', 450000.00, 'aprobado', 3),
('Remodelación Oficinas', 'Pintura, pisos y mobiliario', 85000.00, 'revision', 3),
('Proyecto Torre Sur', 'Construcción 12 pisos zona sur', 2300000.00, 'borrador', 3);

INSERT INTO alertas (mensaje, tipo, usuario_id) VALUES
('Presupuesto "Obra Norte" fue aprobado', 'success', 3),
('Presupuesto "Remodelación Oficinas" enviado a revisión', 'info', 2);
