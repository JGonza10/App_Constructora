const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/gastos?obra_id=X  — todos los gastos de una obra
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `SELECT g.*, u.nombre AS registrado_por_nombre, p.nombre AS proveedor_nombre
           FROM gastos g
           LEFT JOIN usuarios u ON u.id = g.registrado_por
           LEFT JOIN proveedores p ON p.id = g.proveedor_id`;
  let params = [];
  if (obra_id) { q += ' WHERE g.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY g.fecha DESC';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener gastos' });
    res.json(rows);
  });
});

// GET /api/gastos/resumen/:obra_id  — totales por categoría
router.get('/resumen/:obra_id', auth, (req, res) => {
  db.query(`
    SELECT categoria,
           COUNT(*) AS registros,
           SUM(monto) AS total
    FROM gastos WHERE obra_id = ?
    GROUP BY categoria
    ORDER BY total DESC
  `, [req.params.obra_id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    res.json(rows);
  });
});

// POST /api/gastos
router.post('/', auth, (req, res) => {
  const { obra_id, categoria, concepto, monto, fecha, proveedor_id, notas } = req.body;
  if (!obra_id || !categoria || !concepto || !monto || !fecha) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos' });
  }
  db.query(`
    INSERT INTO gastos (obra_id,categoria,concepto,monto,fecha,proveedor_id,notas,registrado_por)
    VALUES (?,?,?,?,?,?,?,?)`,
    [obra_id, categoria, concepto, monto, fecha, proveedor_id||null, notas||null, req.usuario.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al registrar gasto' });
      res.status(201).json({ mensaje: 'Gasto registrado', id: r.insertId });
    }
  );
});

// PUT /api/gastos/:id
router.put('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  const { categoria, concepto, monto, fecha, proveedor_id, notas } = req.body;
  db.query(`
    UPDATE gastos SET categoria=?,concepto=?,monto=?,fecha=?,proveedor_id=?,notas=?
    WHERE id=?`,
    [categoria, concepto, monto, fecha, proveedor_id||null, notas||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Gasto actualizado' });
    }
  );
});

// DELETE /api/gastos/:id
router.delete('/:id', auth, rol('admin'), (req, res) => {
  db.query('DELETE FROM gastos WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Gasto eliminado' });
  });
});

module.exports = router;
