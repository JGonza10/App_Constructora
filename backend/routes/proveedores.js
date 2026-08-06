const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// ─── PROVEEDORES ─────────────────────────────────────────────

// GET /api/proveedores
router.get('/', auth, (req, res) => {
  db.query(`
    SELECT p.*,
      COUNT(o.id) AS total_ordenes,
      COALESCE(SUM(o.monto_real), SUM(o.monto_estimado), 0) AS monto_total
    FROM proveedores p
    LEFT JOIN ordenes_compra o ON o.proveedor_id = p.id
    WHERE p.activo = TRUE
    GROUP BY p.id
    ORDER BY p.nombre`,
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error al obtener proveedores' });
      res.json(rows);
    }
  );
});

// POST /api/proveedores
router.post('/', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, contacto, email, telefono, rfc, categoria, notas } = req.body;
  if (!nombre || !categoria) return res.status(400).json({ mensaje: 'Nombre y categoría son requeridos' });
  db.query(
    'INSERT INTO proveedores (nombre,contacto,email,telefono,rfc,categoria,notas) VALUES (?,?,?,?,?,?,?)',
    [nombre, contacto||null, email||null, telefono||null, rfc||null, categoria, notas||null],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear proveedor' });
      res.status(201).json({ mensaje: 'Proveedor creado', id: r.insertId });
    }
  );
});

// PUT /api/proveedores/:id
router.put('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  const { nombre, contacto, email, telefono, rfc, categoria, notas } = req.body;
  db.query(
    'UPDATE proveedores SET nombre=?,contacto=?,email=?,telefono=?,rfc=?,categoria=?,notas=? WHERE id=?',
    [nombre, contacto||null, email||null, telefono||null, rfc||null, categoria, notas||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Proveedor actualizado' });
    }
  );
});

// DELETE /api/proveedores/:id  (desactivar)
router.delete('/:id', auth, rol('admin'), (req, res) => {
  db.query('UPDATE proveedores SET activo=FALSE WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Proveedor desactivado' });
  });
});

// ─── ÓRDENES DE COMPRA ───────────────────────────────────────

// GET /api/proveedores/ordenes?obra_id=X
router.get('/ordenes', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `
    SELECT oc.*, p.nombre AS proveedor_nombre, o.nombre AS obra_nombre, u.nombre AS creado_por_nombre
    FROM ordenes_compra oc
    JOIN proveedores p ON p.id = oc.proveedor_id
    JOIN obras o ON o.id = oc.obra_id
    LEFT JOIN usuarios u ON u.id = oc.creado_por`;
  let params = [];
  if (obra_id) { q += ' WHERE oc.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY oc.fecha_pedido DESC';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener órdenes' });
    res.json(rows);
  });
});

// POST /api/proveedores/ordenes
router.post('/ordenes', auth, rol('admin', 'supervisor'), (req, res) => {
  const { obra_id, proveedor_id, concepto, monto_estimado, fecha_pedido, fecha_entrega, notas } = req.body;
  if (!obra_id || !proveedor_id || !concepto || !fecha_pedido) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos' });
  }
  db.query(`
    INSERT INTO ordenes_compra
      (obra_id,proveedor_id,concepto,monto_estimado,fecha_pedido,fecha_entrega,notas,creado_por)
    VALUES (?,?,?,?,?,?,?,?)`,
    [obra_id, proveedor_id, concepto, monto_estimado||null, fecha_pedido,
     fecha_entrega||null, notas||null, req.usuario.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear orden' });
      res.status(201).json({ mensaje: 'Orden creada', id: r.insertId });
    }
  );
});

// PATCH /api/proveedores/ordenes/:id/estado
router.patch('/ordenes/:id/estado', auth, rol('admin', 'supervisor'), (req, res) => {
  const { estado, monto_real, fecha_entrega } = req.body;
  db.query(
    'UPDATE ordenes_compra SET estado=?,monto_real=?,fecha_entrega=? WHERE id=?',
    [estado, monto_real||null, fecha_entrega||null, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error al actualizar orden' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrada' });
      res.json({ mensaje: 'Orden actualizada' });
    }
  );
});

module.exports = router;
