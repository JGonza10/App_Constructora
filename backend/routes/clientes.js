const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/clientes
router.get('/', auth, (req, res) => {
  db.query(
    `SELECT c.*,
       COUNT(o.id) AS total_obras,
       COALESCE(SUM(o.monto_contrato),0) AS monto_total
     FROM clientes c
     LEFT JOIN obras o ON o.cliente_id = c.id
     WHERE c.activo = TRUE
     GROUP BY c.id
     ORDER BY c.nombre`,
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error al obtener clientes' });
      res.json(rows);
    }
  );
});

// GET /api/clientes/:id
router.get('/:id', auth, (req, res) => {
  db.query('SELECT * FROM clientes WHERE id = ?', [req.params.id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!rows.length) return res.status(404).json({ mensaje: 'Cliente no encontrado' });
    res.json(rows[0]);
  });
});

// POST /api/clientes
router.post('/', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, email, telefono, rfc, tipo, direccion, notas } = req.body;
  if (!nombre) return res.status(400).json({ mensaje: 'El nombre es requerido' });
  db.query(
    'INSERT INTO clientes (nombre,email,telefono,rfc,tipo,direccion,notas) VALUES (?,?,?,?,?,?,?)',
    [nombre, email||null, telefono||null, rfc||null, tipo||'persona_fisica', direccion||null, notas||null],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear cliente' });
      res.status(201).json({ mensaje: 'Cliente creado', id: r.insertId });
    }
  );
});

// PUT /api/clientes/:id
router.put('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, email, telefono, rfc, tipo, direccion, notas } = req.body;
  db.query(
    'UPDATE clientes SET nombre=?,email=?,telefono=?,rfc=?,tipo=?,direccion=?,notas=? WHERE id=?',
    [nombre, email||null, telefono||null, rfc||null, tipo||'persona_fisica', direccion||null, notas||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Cliente actualizado' });
    }
  );
});

// DELETE /api/clientes/:id  (desactivar, no eliminar)
router.delete('/:id', auth, rol('admin'), (req, res) => {
  db.query('UPDATE clientes SET activo=FALSE WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Cliente desactivado' });
  });
});

module.exports = router;
