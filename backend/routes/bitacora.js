const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/bitacora?obra_id=X
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `
    SELECT b.*, u.nombre AS registrado_por_nombre, o.nombre AS obra_nombre
    FROM bitacora b
    LEFT JOIN usuarios u ON u.id = b.registrado_por
    LEFT JOIN obras o ON o.id = b.obra_id`;
  let params = [];
  if (obra_id) { q += ' WHERE b.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY b.fecha DESC';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener bitácora' });
    res.json(rows);
  });
});

// GET /api/bitacora/:id
router.get('/:id', auth, (req, res) => {
  db.query(`
    SELECT b.*, u.nombre AS registrado_por_nombre
    FROM bitacora b LEFT JOIN usuarios u ON u.id = b.registrado_por
    WHERE b.id=?`, [req.params.id],
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (!rows.length) return res.status(404).json({ mensaje: 'Registro no encontrado' });
      res.json(rows[0]);
    }
  );
});

// POST /api/bitacora
router.post('/', auth, (req, res) => {
  const { obra_id, fecha, clima, personal_qty, actividades, incidencias, materiales, notas } = req.body;
  if (!obra_id || !fecha || !actividades) {
    return res.status(400).json({ mensaje: 'obra_id, fecha y actividades son requeridos' });
  }
  // Evitar duplicado de fecha por obra
  db.query('SELECT id FROM bitacora WHERE obra_id=? AND fecha=?', [obra_id, fecha], (err, existe) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (existe.length) return res.status(409).json({ mensaje: 'Ya existe un registro para esta fecha en la obra' });

    db.query(`
      INSERT INTO bitacora (obra_id,fecha,clima,personal_qty,actividades,incidencias,materiales,notas,registrado_por)
      VALUES (?,?,?,?,?,?,?,?,?)`,
      [obra_id, fecha, clima||'soleado', personal_qty||0,
       actividades, incidencias||null, materiales||null, notas||null, req.usuario.id],
      (err2, r) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al crear registro' });
        res.status(201).json({ mensaje: 'Registro de bitácora creado', id: r.insertId });
      }
    );
  });
});

// PUT /api/bitacora/:id  — solo el mismo día o admin
router.put('/:id', auth, (req, res) => {
  const { clima, personal_qty, actividades, incidencias, materiales, notas } = req.body;
  db.query(`
    UPDATE bitacora SET clima=?,personal_qty=?,actividades=?,incidencias=?,materiales=?,notas=?
    WHERE id=?`,
    [clima||'soleado', personal_qty||0, actividades, incidencias||null, materiales||null, notas||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Registro actualizado' });
    }
  );
});

// DELETE /api/bitacora/:id  — solo admin
router.delete('/:id', auth, rol('admin'), (req, res) => {
  db.query('DELETE FROM bitacora WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Registro eliminado' });
  });
});

module.exports = router;
