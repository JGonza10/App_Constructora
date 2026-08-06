const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');

// GET /api/avance?obra_id=X
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `SELECT a.*, u.nombre AS reportado_por_nombre
           FROM avance_obra a
           LEFT JOIN usuarios u ON u.id = a.reportado_por`;
  let params = [];
  if (obra_id) { q += ' WHERE a.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY a.semana DESC, a.etapa';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener avances' });
    res.json(rows);
  });
});

// POST /api/avance
router.post('/', auth, (req, res) => {
  const { obra_id, semana, etapa, porcentaje, descripcion } = req.body;
  if (!obra_id || !semana || !etapa || porcentaje === undefined) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos' });
  }
  db.query(`
    INSERT INTO avance_obra (obra_id,semana,etapa,porcentaje,descripcion,reportado_por)
    VALUES (?,?,?,?,?,?)`,
    [obra_id, semana, etapa, porcentaje, descripcion||null, req.usuario.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al registrar avance' });
      res.status(201).json({ mensaje: 'Avance registrado', id: r.insertId });
    }
  );
});

// PUT /api/avance/:id
router.put('/:id', auth, (req, res) => {
  const { etapa, porcentaje, descripcion } = req.body;
  db.query(
    'UPDATE avance_obra SET etapa=?,porcentaje=?,descripcion=? WHERE id=?',
    [etapa, porcentaje, descripcion||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Avance actualizado' });
    }
  );
});

// DELETE /api/avance/:id
router.delete('/:id', auth, (req, res) => {
  db.query('DELETE FROM avance_obra WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Avance eliminado' });
  });
});

module.exports = router;
