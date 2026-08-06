const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/tareas?obra_id=X
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `
    SELECT t.*, u.nombre AS responsable_nombre, o.nombre AS obra_nombre
    FROM tareas t
    LEFT JOIN usuarios u ON u.id = t.responsable_id
    LEFT JOIN obras o ON o.id = t.obra_id`;
  let params = [];
  if (obra_id) { q += ' WHERE t.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY t.fecha_fin, t.prioridad DESC';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener tareas' });
    res.json(rows);
  });
});

// GET /api/tareas/atrasadas  — tareas vencidas sin terminar
router.get('/atrasadas', auth, rol('admin', 'supervisor'), (req, res) => {
  db.query(`
    SELECT t.*, u.nombre AS responsable_nombre, o.nombre AS obra_nombre
    FROM tareas t
    LEFT JOIN usuarios u ON u.id = t.responsable_id
    JOIN obras o ON o.id = t.obra_id
    WHERE t.fecha_fin < CURDATE()
      AND t.estado NOT IN ('terminada')
    ORDER BY t.fecha_fin`,
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      res.json(rows);
    }
  );
});

// POST /api/tareas
router.post('/', auth, (req, res) => {
  const { obra_id, titulo, descripcion, responsable_id, fecha_inicio, fecha_fin, prioridad } = req.body;
  if (!obra_id || !titulo) return res.status(400).json({ mensaje: 'obra_id y título son requeridos' });
  db.query(`
    INSERT INTO tareas (obra_id,titulo,descripcion,responsable_id,fecha_inicio,fecha_fin,prioridad,creado_por)
    VALUES (?,?,?,?,?,?,?,?)`,
    [obra_id, titulo, descripcion||null, responsable_id||null,
     fecha_inicio||null, fecha_fin||null, prioridad||'media', req.usuario.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear tarea' });
      res.status(201).json({ mensaje: 'Tarea creada', id: r.insertId });
    }
  );
});

// PATCH /api/tareas/:id/estado
router.patch('/:id/estado', auth, (req, res) => {
  const { estado } = req.body;
  const validos = ['pendiente', 'en_curso', 'terminada', 'atrasada'];
  if (!validos.includes(estado)) return res.status(400).json({ mensaje: 'Estado no válido' });
  db.query('UPDATE tareas SET estado=? WHERE id=?', [estado, req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
    res.json({ mensaje: `Tarea marcada como: ${estado}` });
  });
});

// PUT /api/tareas/:id
router.put('/:id', auth, (req, res) => {
  const { titulo, descripcion, responsable_id, fecha_inicio, fecha_fin, prioridad, estado } = req.body;
  db.query(`
    UPDATE tareas SET titulo=?,descripcion=?,responsable_id=?,
      fecha_inicio=?,fecha_fin=?,prioridad=?,estado=?
    WHERE id=?`,
    [titulo, descripcion||null, responsable_id||null,
     fecha_inicio||null, fecha_fin||null, prioridad||'media', estado||'pendiente', req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar tarea' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
      res.json({ mensaje: 'Tarea actualizada' });
    }
  );
});

// DELETE /api/tareas/:id
router.delete('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  db.query('DELETE FROM tareas WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
    res.json({ mensaje: 'Tarea eliminada' });
  });
});

module.exports = router;
