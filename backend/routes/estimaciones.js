const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// ─── CATÁLOGO DE MATERIALES ──────────────────────────────────

// GET /api/estimaciones/catalogo
router.get('/catalogo', auth, (req, res) => {
  db.query('SELECT * FROM catalogo_materiales ORDER BY categoria, nombre', (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener catálogo' });
    res.json(rows);
  });
});

// POST /api/estimaciones/catalogo  (agregar material nuevo al catálogo)
router.post('/catalogo', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, unidad, precio_unitario, categoria } = req.body;
  if (!nombre || !unidad || !precio_unitario || !categoria) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos' });
  }
  db.query(
    'INSERT INTO catalogo_materiales (nombre,unidad,precio_unitario,categoria) VALUES (?,?,?,?)',
    [nombre, unidad, precio_unitario, categoria],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear material' });
      res.status(201).json({ mensaje: 'Material agregado al catálogo', id: r.insertId });
    }
  );
});

// PUT /api/estimaciones/catalogo/:id  (actualizar precio de mercado)
router.put('/catalogo/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  const { precio_unitario } = req.body;
  if (!precio_unitario) return res.status(400).json({ mensaje: 'Falta precio_unitario' });
  db.query(
    'UPDATE catalogo_materiales SET precio_unitario=? WHERE id=?',
    [precio_unitario, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar precio' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Precio actualizado' });
    }
  );
});

// ─── ESTIMACIONES POR OBRA ───────────────────────────────────

// GET /api/estimaciones?obra_id=X
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `SELECT e.*, u.nombre AS creado_por_nombre
           FROM estimaciones e
           LEFT JOIN usuarios u ON u.id = e.creado_por`;
  let params = [];
  if (obra_id) { q += ' WHERE e.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY e.creado_en DESC';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener estimaciones' });
    res.json(rows);
  });
});

// GET /api/estimaciones/:id  (con sus items)
router.get('/:id', auth, (req, res) => {
  db.query('SELECT * FROM estimaciones WHERE id=?', [req.params.id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!rows.length) return res.status(404).json({ mensaje: 'No encontrada' });

    db.query(`
      SELECT ei.*, m.nombre AS material_nombre, m.unidad
      FROM estimacion_items ei
      JOIN catalogo_materiales m ON m.id = ei.material_id
      WHERE ei.estimacion_id = ?`,
      [req.params.id],
      (err2, items) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al obtener items' });
        res.json({ ...rows[0], items });
      }
    );
  });
});

// POST /api/estimaciones  (crear con items en un solo request)
// body: { obra_id, nombre, notas, items: [{ material_id, cantidad }] }
router.post('/', auth, (req, res) => {
  const { obra_id, nombre, notas, items } = req.body;
  if (!obra_id || !nombre || !items || !items.length) {
    return res.status(400).json({ mensaje: 'obra_id, nombre e items son requeridos' });
  }

  const materialIds = items.map(i => i.material_id);
  db.query(
    `SELECT * FROM catalogo_materiales WHERE id IN (${materialIds.map(() => '?').join(',')})`,
    materialIds,
    (err, materiales) => {
      if (err) return res.status(500).json({ mensaje: 'Error al validar materiales' });

      const mapaPrecios = {};
      materiales.forEach(m => { mapaPrecios[m.id] = Number(m.precio_unitario); });

      let total = 0;
      const itemsCalculados = items.map(i => {
        const precio = mapaPrecios[i.material_id] || 0;
        const subtotal = precio * Number(i.cantidad);
        total += subtotal;
        return { ...i, precio_unitario: precio, subtotal };
      });

      db.query(
        'INSERT INTO estimaciones (obra_id,nombre,notas,total,creado_por) VALUES (?,?,?,?,?)',
        [obra_id, nombre, notas || null, total, req.usuario.id],
        (err2, r) => {
          if (err2) return res.status(500).json({ mensaje: 'Error al crear estimación' });
          const estimacionId = r.insertId;

          const values = itemsCalculados.map(i => [estimacionId, i.material_id, i.cantidad, i.precio_unitario, i.subtotal]);
          db.query(
            'INSERT INTO estimacion_items (estimacion_id,material_id,cantidad,precio_unitario,subtotal) VALUES ?',
            [values],
            (err3) => {
              if (err3) return res.status(500).json({ mensaje: 'Error al guardar items' });
              res.status(201).json({ mensaje: 'Estimación creada', id: estimacionId, total });
            }
          );
        }
      );
    }
  );
});

// DELETE /api/estimaciones/:id
router.delete('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  db.query('DELETE FROM estimaciones WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
    res.json({ mensaje: 'Estimación eliminada' });
  });
});

module.exports = router;
