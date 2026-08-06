const express = require('express');
const router = express.Router();
const db = require('../db');
const verificarToken = require('../middleware/auth');
const verificarRol = require('../middleware/roles');

// GET /api/presupuestos  (filtrado por rol)
router.get('/', verificarToken, (req, res) => {
  const { rol, id } = req.usuario;
  let query, params;

  if (rol === 'empleado') {
    // Empleado solo ve sus propios presupuestos
    query = `
      SELECT p.*, u.nombre AS creador, r.nombre AS revisor, o.nombre AS obra_nombre
      FROM presupuestos p
      JOIN usuarios u ON p.creado_por = u.id
      LEFT JOIN usuarios r ON p.revisado_por = r.id
      LEFT JOIN obras o ON o.id = p.obra_id
      WHERE p.creado_por = ?
      ORDER BY p.actualizado_en DESC
    `;
    params = [id];
  } else {
    // Admin y supervisor ven todos
    query = `
      SELECT p.*, u.nombre AS creador, r.nombre AS revisor, o.nombre AS obra_nombre
      FROM presupuestos p
      JOIN usuarios u ON p.creado_por = u.id
      LEFT JOIN usuarios r ON p.revisado_por = r.id
      LEFT JOIN obras o ON o.id = p.obra_id
      ORDER BY p.actualizado_en DESC
    `;
    params = [];
  }

  db.query(query, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener presupuestos' });
    res.json(rows);
  });
});

// GET /api/presupuestos/:id
router.get('/:id', verificarToken, (req, res) => {
  db.query(
    `SELECT p.*, u.nombre AS creador, r.nombre AS revisor
     FROM presupuestos p
     JOIN usuarios u ON p.creado_por = u.id
     LEFT JOIN usuarios r ON p.revisado_por = r.id
     WHERE p.id = ?`,
    [req.params.id],
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (rows.length === 0) return res.status(404).json({ mensaje: 'Presupuesto no encontrado' });

      // Empleado solo puede ver los suyos
      if (req.usuario.rol === 'empleado' && rows[0].creado_por !== req.usuario.id) {
        return res.status(403).json({ mensaje: 'Acceso denegado' });
      }
      res.json(rows[0]);
    }
  );
});

// POST /api/presupuestos  (empleados y supervisores pueden crear)
router.post('/', verificarToken, verificarRol('admin', 'supervisor', 'empleado'), (req, res) => {
  const { titulo, descripcion, monto, obra_id } = req.body;
  if (!titulo || !monto) {
    return res.status(400).json({ mensaje: 'Título y monto son requeridos' });
  }
  if (isNaN(monto) || monto <= 0) {
    return res.status(400).json({ mensaje: 'El monto debe ser un número positivo' });
  }

  db.query(
    'INSERT INTO presupuestos (titulo, descripcion, monto, obra_id, creado_por) VALUES (?, ?, ?, ?, ?)',
    [titulo, descripcion || null, monto, obra_id || null, req.usuario.id],
    (err, result) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear presupuesto' });
      res.status(201).json({ mensaje: 'Presupuesto creado', id: result.insertId });
    }
  );
});

// PUT /api/presupuestos/:id  (editar datos — solo si está en borrador)
router.put('/:id', verificarToken, (req, res) => {
  const { titulo, descripcion, monto } = req.body;
  const usuarioId = req.usuario.id;
  const rol = req.usuario.rol;

  db.query('SELECT * FROM presupuestos WHERE id = ?', [req.params.id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (rows.length === 0) return res.status(404).json({ mensaje: 'No encontrado' });

    const p = rows[0];

    // Solo el creador puede editar, y solo si está en borrador
    if (rol === 'empleado' && p.creado_por !== usuarioId) {
      return res.status(403).json({ mensaje: 'No puedes editar un presupuesto ajeno' });
    }
    if (p.estado !== 'borrador') {
      return res.status(400).json({ mensaje: 'Solo se pueden editar presupuestos en borrador' });
    }

    db.query(
      'UPDATE presupuestos SET titulo = ?, descripcion = ?, monto = ? WHERE id = ?',
      [titulo || p.titulo, descripcion || p.descripcion, monto || p.monto, req.params.id],
      (err2) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al actualizar' });
        res.json({ mensaje: 'Presupuesto actualizado' });
      }
    );
  });
});

// PATCH /api/presupuestos/:id/estado  (cambiar estado)
router.patch('/:id/estado', verificarToken, (req, res) => {
  const { estado, comentario_revision } = req.body;
  const { rol, id: usuarioId } = req.usuario;

  const transicionesValidas = {
    empleado:   { borrador: ['revision'] },
    supervisor: { revision: ['aprobado', 'rechazado'] },
    admin:      { borrador: ['revision'], revision: ['aprobado', 'rechazado'] }
  };

  db.query('SELECT * FROM presupuestos WHERE id = ?', [req.params.id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (rows.length === 0) return res.status(404).json({ mensaje: 'No encontrado' });

    const p = rows[0];
    const permitidos = transicionesValidas[rol]?.[p.estado] || [];

    if (!permitidos.includes(estado)) {
      return res.status(400).json({
        mensaje: `Transición no permitida: ${p.estado} → ${estado} para rol ${rol}`
      });
    }

    const revisadoPor = ['aprobado', 'rechazado'].includes(estado) ? usuarioId : null;

    db.query(
      'UPDATE presupuestos SET estado = ?, revisado_por = ?, comentario_revision = ? WHERE id = ?',
      [estado, revisadoPor, comentario_revision || null, req.params.id],
      (err2) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al cambiar estado' });
        res.json({ mensaje: `Presupuesto marcado como: ${estado}` });
      }
    );
  });
});

// DELETE /api/presupuestos/:id  (solo admin, solo si está en borrador)
router.delete('/:id', verificarToken, verificarRol('admin'), (req, res) => {
  db.query(
    'DELETE FROM presupuestos WHERE id = ? AND estado = "borrador"',
    [req.params.id],
    (err, result) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (result.affectedRows === 0) {
        return res.status(400).json({ mensaje: 'Solo se pueden eliminar presupuestos en borrador' });
      }
      res.json({ mensaje: 'Presupuesto eliminado' });
    }
  );
});

module.exports = router;
