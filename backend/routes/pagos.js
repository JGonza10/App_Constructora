const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/pagos?obra_id=X
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `SELECT p.*, o.nombre AS obra_nombre, c.nombre AS cliente_nombre
           FROM pagos_cliente p
           JOIN obras o ON o.id = p.obra_id
           JOIN clientes c ON c.id = o.cliente_id`;
  let params = [];
  if (obra_id) { q += ' WHERE p.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY p.fecha_programada';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener pagos' });
    res.json(rows);
  });
});

// GET /api/pagos/pendientes  — todos los pagos vencidos o próximos (30 días)
router.get('/pendientes', auth, rol('admin', 'supervisor'), (req, res) => {
  db.query(`
    SELECT p.*, o.nombre AS obra_nombre, c.nombre AS cliente_nombre
    FROM pagos_cliente p
    JOIN obras o ON o.id = p.obra_id
    JOIN clientes c ON c.id = o.cliente_id
    WHERE p.estado IN ('pendiente','vencido')
      AND p.fecha_programada <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
    ORDER BY p.fecha_programada
  `, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    res.json(rows);
  });
});

// POST /api/pagos
router.post('/', auth, rol('admin', 'supervisor'), (req, res) => {
  const { obra_id, concepto, monto, fecha_programada, notas } = req.body;
  if (!obra_id || !concepto || !monto || !fecha_programada) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos' });
  }
  db.query(`
    INSERT INTO pagos_cliente (obra_id,concepto,monto,fecha_programada,notas)
    VALUES (?,?,?,?,?)`,
    [obra_id, concepto, monto, fecha_programada, notas||null],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear pago' });
      res.status(201).json({ mensaje: 'Pago programado', id: r.insertId });
    }
  );
});

// PATCH /api/pagos/:id/recibir  — marcar como recibido
router.patch('/:id/recibir', auth, rol('admin', 'supervisor'), (req, res) => {
  const fecha = req.body.fecha_recibido || new Date().toISOString().split('T')[0];
  db.query(
    "UPDATE pagos_cliente SET estado='recibido', fecha_recibido=? WHERE id=?",
    [fecha, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Pago marcado como recibido' });
    }
  );
});

// PUT /api/pagos/:id
router.put('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  const { concepto, monto, fecha_programada, estado, notas } = req.body;
  db.query(
    'UPDATE pagos_cliente SET concepto=?,monto=?,fecha_programada=?,estado=?,notas=? WHERE id=?',
    [concepto, monto, fecha_programada, estado, notas||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Pago actualizado' });
    }
  );
});

// DELETE /api/pagos/:id
router.delete('/:id', auth, rol('admin'), (req, res) => {
  db.query('DELETE FROM pagos_cliente WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Pago eliminado' });
  });
});

module.exports = router;
