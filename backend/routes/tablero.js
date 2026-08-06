const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/tablero  — vista ejecutiva completa para la arquitecto
router.get('/', auth, rol('admin', 'supervisor'), (req, res) => {
  const queries = {

    // 1. Resumen de obras por estado
    obrasPorEstado: `
      SELECT estado, COUNT(*) AS cantidad, COALESCE(SUM(monto_contrato),0) AS monto_total
      FROM obras GROUP BY estado`,

    // 2. Obras activas con KPIs financieros
    obrasActivas: `
      SELECT o.id, o.nombre, o.tipo, o.estado, o.avance_porcentaje,
        o.monto_contrato, o.fecha_fin_estimada,
        c.nombre AS cliente,
        COALESCE(SUM(g.monto),0) AS gasto_real,
        ROUND(COALESCE(SUM(g.monto),0) / NULLIF(o.monto_contrato,0) * 100, 1) AS pct_gastado,
        o.monto_contrato - COALESCE(SUM(g.monto),0) AS saldo
      FROM obras o
      JOIN clientes c ON c.id = o.cliente_id
      LEFT JOIN gastos g ON g.obra_id = o.id
      WHERE o.estado IN ('activa','pausada')
      GROUP BY o.id
      ORDER BY o.fecha_fin_estimada`,

    // 3. Pagos próximos (30 días) o vencidos
    pagosAlerta: `
      SELECT p.id, p.concepto, p.monto, p.fecha_programada, p.estado,
        o.nombre AS obra_nombre, c.nombre AS cliente_nombre,
        DATEDIFF(p.fecha_programada, CURDATE()) AS dias_restantes
      FROM pagos_cliente p
      JOIN obras o ON o.id = p.obra_id
      JOIN clientes c ON c.id = o.cliente_id
      WHERE p.estado IN ('pendiente','vencido')
        AND p.fecha_programada <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
      ORDER BY p.fecha_programada`,

    // 4. Tareas atrasadas
    tareasAtrasadas: `
      SELECT t.id, t.titulo, t.fecha_fin, t.prioridad,
        o.nombre AS obra_nombre, u.nombre AS responsable
      FROM tareas t
      JOIN obras o ON o.id = t.obra_id
      LEFT JOIN usuarios u ON u.id = t.responsable_id
      WHERE t.fecha_fin < CURDATE() AND t.estado NOT IN ('terminada')
      ORDER BY t.fecha_fin LIMIT 10`,

    // 5. Gastos del mes actual por categoría
    gastosMes: `
      SELECT categoria, SUM(monto) AS total
      FROM gastos
      WHERE MONTH(fecha) = MONTH(CURDATE()) AND YEAR(fecha) = YEAR(CURDATE())
      GROUP BY categoria
      ORDER BY total DESC`,

    // 6. Rentabilidad estimada por obra activa
    rentabilidad: `
      SELECT o.id, o.nombre,
        o.monto_contrato,
        COALESCE(SUM(g.monto),0) AS egresos,
        COALESCE(SUM(CASE WHEN pc.estado='recibido' THEN pc.monto ELSE 0 END),0) AS cobrado,
        o.monto_contrato - COALESCE(SUM(g.monto),0) AS utilidad_estimada
      FROM obras o
      LEFT JOIN gastos g ON g.obra_id = o.id
      LEFT JOIN pagos_cliente pc ON pc.obra_id = o.id
      WHERE o.estado = 'activa'
      GROUP BY o.id`
  };

  const resultado = {};
  const keys = Object.keys(queries);
  let completados = 0;
  let errorGlobal = false;

  keys.forEach(key => {
    db.query(queries[key], (err, rows) => {
      if (err && !errorGlobal) {
        errorGlobal = true;
        return res.status(500).json({ mensaje: `Error en consulta: ${key}`, detalle: err.message });
      }
      if (!errorGlobal) {
        resultado[key] = rows;
        completados++;
        if (completados === keys.length) res.json(resultado);
      }
    });
  });
});

module.exports = router;
