const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const db = require('../db');
const verificarToken = require('../middleware/auth');
const verificarRol = require('../middleware/roles');

if (!process.env.JWT_SECRET) {
  throw new Error(
    'Falta configurar JWT_SECRET en las variables de entorno. ' +
    'Copia backend/.env.example a backend/.env y define un secreto propio antes de iniciar el servidor.'
  );
}
const SECRET = process.env.JWT_SECRET;

// POST /api/usuarios/registro  (solo admin puede crear usuarios)
router.post('/registro', verificarToken, verificarRol('admin'), async (req, res) => {
  const { nombre, email, password, rol } = req.body;
  if (!nombre || !email || !password || !rol) {
    return res.status(400).json({ mensaje: 'Todos los campos son requeridos' });
  }
  const rolesValidos = ['admin', 'supervisor', 'empleado'];
  if (!rolesValidos.includes(rol)) {
    return res.status(400).json({ mensaje: 'Rol no válido' });
  }
  try {
    const hash = await bcrypt.hash(password, 10);
    db.query(
      'INSERT INTO usuarios (nombre, email, password, rol) VALUES (?, ?, ?, ?)',
      [nombre, email, hash, rol],
      (err, result) => {
        if (err) {
          if (err.code === 'ER_DUP_ENTRY') {
            return res.status(409).json({ mensaje: 'El email ya está registrado' });
          }
          return res.status(500).json({ mensaje: 'Error al registrar usuario' });
        }
        res.status(201).json({ mensaje: 'Usuario registrado', id: result.insertId });
      }
    );
  } catch (err) {
    res.status(500).json({ mensaje: 'Error interno del servidor' });
  }
});

// POST /api/usuarios/login
router.post('/login', (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ mensaje: 'Email y password requeridos' });
  }
  db.query('SELECT * FROM usuarios WHERE email = ? AND activo = TRUE', [email], async (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (rows.length === 0) return res.status(401).json({ mensaje: 'Credenciales inválidas' });

    const usuario = rows[0];
    const coincide = await bcrypt.compare(password, usuario.password);
    if (!coincide) return res.status(401).json({ mensaje: 'Credenciales inválidas' });

    const token = jwt.sign(
      { id: usuario.id, nombre: usuario.nombre, email: usuario.email, rol: usuario.rol },
      SECRET,
      { expiresIn: '8h' }
    );
    res.json({
      token,
      usuario: { id: usuario.id, nombre: usuario.nombre, email: usuario.email, rol: usuario.rol }
    });
  });
});

// GET /api/usuarios/perfil  (usuario autenticado ve su perfil)
router.get('/perfil', verificarToken, (req, res) => {
  db.query(
    'SELECT id, nombre, email, rol, creado_en FROM usuarios WHERE id = ?',
    [req.usuario.id],
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (rows.length === 0) return res.status(404).json({ mensaje: 'Usuario no encontrado' });
      res.json(rows[0]);
    }
  );
});

// GET /api/usuarios  (solo admin y supervisor)
router.get('/', verificarToken, verificarRol('admin', 'supervisor'), (req, res) => {
  db.query(
    'SELECT id, nombre, email, rol, activo, creado_en FROM usuarios ORDER BY creado_en DESC',
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      res.json(rows);
    }
  );
});

// PUT /api/usuarios/:id/estado  (solo admin puede activar/desactivar)
router.put('/:id/estado', verificarToken, verificarRol('admin'), (req, res) => {
  const { activo } = req.body;
  db.query(
    'UPDATE usuarios SET activo = ? WHERE id = ?',
    [activo, req.params.id],
    (err, result) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (result.affectedRows === 0) return res.status(404).json({ mensaje: 'Usuario no encontrado' });
      res.json({ mensaje: `Usuario ${activo ? 'activado' : 'desactivado'}` });
    }
  );
});

module.exports = router;
