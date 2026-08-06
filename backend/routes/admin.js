const express = require('express');
const router = express.Router();
const db = require('../db');
const verificarToken = require('../middleware/auth');
const verificarRol = require('../middleware/roles');
const ExcelJS = require('exceljs');
const PDFDocument = require('pdfkit');

// GET /api/admin/estadisticas  (admin y supervisor)
router.get('/estadisticas', verificarToken, verificarRol('admin', 'supervisor'), (req, res) => {
  const queries = {
    totalPresupuestos: 'SELECT COUNT(*) AS total FROM presupuestos',
    porEstado: 'SELECT estado, COUNT(*) AS cantidad FROM presupuestos GROUP BY estado',
    montoTotal: 'SELECT SUM(monto) AS total FROM presupuestos WHERE estado = "aprobado"',
    totalUsuarios: 'SELECT COUNT(*) AS total FROM usuarios WHERE activo = TRUE',
    porRol: 'SELECT rol, COUNT(*) AS cantidad FROM usuarios GROUP BY rol'
  };

  const resultados = {};
  const keys = Object.keys(queries);
  let completados = 0;

  keys.forEach(key => {
    db.query(queries[key], (err, rows) => {
      if (!err) resultados[key] = rows;
      completados++;
      if (completados === keys.length) {
        res.json(resultados);
      }
    });
  });
});

// GET /api/admin/alertas  (todas las alertas)
router.get('/alertas', verificarToken, verificarRol('admin', 'supervisor'), (req, res) => {
  db.query(
    `SELECT a.*, u.nombre AS usuario_nombre
     FROM alertas a
     LEFT JOIN usuarios u ON a.usuario_id = u.id
     ORDER BY a.creado_en DESC LIMIT 50`,
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      res.json(rows);
    }
  );
});

// POST /api/admin/alertas  (crear alerta — admin y supervisor)
router.post('/alertas', verificarToken, verificarRol('admin', 'supervisor'), (req, res) => {
  const { mensaje, tipo, usuario_id } = req.body;
  if (!mensaje) return res.status(400).json({ mensaje: 'El mensaje es requerido' });

  db.query(
    'INSERT INTO alertas (mensaje, tipo, usuario_id) VALUES (?, ?, ?)',
    [mensaje, tipo || 'info', usuario_id || null],
    (err, result) => {
      if (err) return res.status(500).json({ mensaje: 'Error al crear alerta' });
      res.status(201).json({ mensaje: 'Alerta creada', id: result.insertId });
    }
  );
});

// PATCH /api/admin/alertas/:id/leer
router.patch('/alertas/:id/leer', verificarToken, (req, res) => {
  db.query(
    'UPDATE alertas SET leida = TRUE WHERE id = ?',
    [req.params.id],
    (err) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      res.json({ mensaje: 'Alerta marcada como leída' });
    }
  );
});

// GET /api/admin/exportar/excel
router.get('/exportar/excel', verificarToken, verificarRol('admin', 'supervisor'), async (req, res) => {
  db.query(
    `SELECT p.id, p.titulo, p.descripcion, p.monto, p.estado,
            u.nombre AS creador, r.nombre AS revisor,
            p.comentario_revision, p.creado_en
     FROM presupuestos p
     JOIN usuarios u ON p.creado_por = u.id
     LEFT JOIN usuarios r ON p.revisado_por = r.id
     ORDER BY p.creado_en DESC`,
    async (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error al exportar' });

      const workbook = new ExcelJS.Workbook();
      const sheet = workbook.addWorksheet('Presupuestos');

      sheet.columns = [
        { header: 'ID', key: 'id', width: 8 },
        { header: 'Título', key: 'titulo', width: 30 },
        { header: 'Descripción', key: 'descripcion', width: 40 },
        { header: 'Monto ($)', key: 'monto', width: 15 },
        { header: 'Estado', key: 'estado', width: 12 },
        { header: 'Creado por', key: 'creador', width: 20 },
        { header: 'Revisado por', key: 'revisor', width: 20 },
        { header: 'Comentario', key: 'comentario_revision', width: 30 },
        { header: 'Fecha', key: 'creado_en', width: 20 }
      ];

      sheet.getRow(1).font = { bold: true };
      rows.forEach(row => sheet.addRow(row));

      res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
      res.setHeader('Content-Disposition', 'attachment; filename=presupuestos.xlsx');
      await workbook.xlsx.write(res);
      res.end();
    }
  );
});

// GET /api/admin/exportar/pdf
router.get('/exportar/pdf', verificarToken, verificarRol('admin', 'supervisor'), (req, res) => {
  db.query(
    `SELECT p.titulo, p.monto, p.estado, u.nombre AS creador, p.creado_en
     FROM presupuestos p
     JOIN usuarios u ON p.creado_por = u.id
     ORDER BY p.creado_en DESC`,
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error al exportar' });

      const doc = new PDFDocument({ margin: 40 });
      res.setHeader('Content-Type', 'application/pdf');
      res.setHeader('Content-Disposition', 'attachment; filename=presupuestos.pdf');
      doc.pipe(res);

      doc.fontSize(18).text('Reporte de Presupuestos', { align: 'center' });
      doc.moveDown();
      doc.fontSize(10).text(`Generado: ${new Date().toLocaleString('es-MX')}`, { align: 'right' });
      doc.moveDown();

      rows.forEach((p, i) => {
        doc.fontSize(12).text(`${i + 1}. ${p.titulo}`);
        doc.fontSize(10)
          .text(`   Monto: $${Number(p.monto).toLocaleString('es-MX')}`)
          .text(`   Estado: ${p.estado}`)
          .text(`   Creado por: ${p.creador}`)
          .text(`   Fecha: ${new Date(p.creado_en).toLocaleDateString('es-MX')}`);
        doc.moveDown(0.5);
      });

      doc.end();
    }
  );
});

module.exports = router;
