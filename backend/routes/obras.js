const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/obras  — listado con KPIs calculados
router.get('/', auth, (req, res) => {
  const { rol: userRol, id: userId } = req.usuario;
  let where = userRol === 'empleado' ? 'WHERE o.responsable_id = ?' : '';
  let params = userRol === 'empleado' ? [userId] : [];

  db.query(`
    SELECT o.*,
      c.nombre AS cliente_nombre, c.telefono AS cliente_tel,
      u.nombre AS responsable_nombre,
      COALESCE(SUM(g.monto),0) AS gasto_real,
      o.monto_contrato - COALESCE(SUM(g.monto),0) AS saldo_presupuesto,
      ROUND(COALESCE(SUM(g.monto),0) / NULLIF(o.monto_contrato,0) * 100, 1) AS pct_gasto
    FROM obras o
    JOIN clientes c ON c.id = o.cliente_id
    LEFT JOIN usuarios u ON u.id = o.responsable_id
    LEFT JOIN gastos g ON g.obra_id = o.id
    ${where}
    GROUP BY o.id
    ORDER BY o.estado, o.fecha_fin_estimada
  `, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener obras' });
    res.json(rows);
  });
});

// GET /api/obras/:id  — detalle completo
router.get('/:id', auth, (req, res) => {
  db.query(`
    SELECT o.*,
      c.nombre AS cliente_nombre, c.email AS cliente_email, c.telefono AS cliente_tel,
      u.nombre AS responsable_nombre,
      cr.nombre AS creado_por_nombre,
      COALESCE(SUM(g.monto),0) AS gasto_real,
      o.monto_contrato - COALESCE(SUM(g.monto),0) AS saldo_presupuesto
    FROM obras o
    JOIN clientes c ON c.id = o.cliente_id
    LEFT JOIN usuarios u ON u.id = o.responsable_id
    LEFT JOIN usuarios cr ON cr.id = o.creado_por
    LEFT JOIN gastos g ON g.obra_id = o.id
    WHERE o.id = ?
    GROUP BY o.id
  `, [req.params.id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!rows.length) return res.status(404).json({ mensaje: 'Obra no encontrada' });
    res.json(rows[0]);
  });
});

// POST /api/obras
router.post('/', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, tipo, cliente_id, responsable_id, monto_contrato,
          fecha_inicio, fecha_fin_estimada, estado, direccion, descripcion } = req.body;
  if (!nombre || !tipo || !cliente_id || !monto_contrato) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos: nombre, tipo, cliente, monto' });
  }
  db.query(`
    INSERT INTO obras
      (nombre,tipo,cliente_id,responsable_id,monto_contrato,fecha_inicio,
       fecha_fin_estimada,estado,direccion,descripcion,creado_por)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)`,
    [nombre, tipo, cliente_id, responsable_id||null, monto_contrato,
     fecha_inicio||null, fecha_fin_estimada||null, estado||'cotizacion',
     direccion||null, descripcion||null, req.usuario.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear obra' });
      res.status(201).json({ mensaje: 'Obra creada', id: r.insertId });
    }
  );
});

// PUT /api/obras/:id
router.put('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, tipo, cliente_id, responsable_id, monto_contrato,
          fecha_inicio, fecha_fin_estimada, fecha_fin_real,
          estado, avance_porcentaje, direccion, descripcion } = req.body;
  db.query(`
    UPDATE obras SET
      nombre=?, tipo=?, cliente_id=?, responsable_id=?, monto_contrato=?,
      fecha_inicio=?, fecha_fin_estimada=?, fecha_fin_real=?,
      estado=?, avance_porcentaje=?, direccion=?, descripcion=?
    WHERE id=?`,
    [nombre, tipo, cliente_id, responsable_id||null, monto_contrato,
     fecha_inicio||null, fecha_fin_estimada||null, fecha_fin_real||null,
     estado, avance_porcentaje||0, direccion||null, descripcion||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar obra' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
      res.json({ mensaje: 'Obra actualizada' });
    }
  );
});

// PATCH /api/obras/:id/avance  — actualizar solo el porcentaje
router.patch('/:id/avance', auth, (req, res) => {
  const { avance_porcentaje } = req.body;
  if (avance_porcentaje === undefined) return res.status(400).json({ mensaje: 'Falta avance_porcentaje' });
  db.query(
    'UPDATE obras SET avance_porcentaje=? WHERE id=?',
    [Math.min(100, Math.max(0, avance_porcentaje)), req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
      res.json({ mensaje: 'Avance actualizado' });
    }
  );
});

module.exports = router;
