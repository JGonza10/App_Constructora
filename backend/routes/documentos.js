const express = require('express');
const router  = express.Router();
const db      = require('../db');
const auth    = require('../middleware/auth');
const rol     = require('../middleware/roles');

// GET /api/documentos?obra_id=X
router.get('/', auth, (req, res) => {
  const { obra_id } = req.query;
  let q = `SELECT d.*, u.nombre AS subido_por_nombre, o.nombre AS obra_nombre
           FROM documentos d
           LEFT JOIN usuarios u ON u.id = d.subido_por
           LEFT JOIN obras o ON o.id = d.obra_id`;
  let params = [];
  if (obra_id) { q += ' WHERE d.obra_id = ?'; params = [obra_id]; }
  q += ' ORDER BY d.categoria, d.creado_en DESC';
  db.query(q, params, (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error al obtener documentos' });
    res.json(rows);
  });
});

// POST /api/documentos
// Nota: este endpoint registra la referencia del archivo (url_archivo).
// La subida física del binario se maneja en el cliente (Drive, S3, disco, etc.)
// y aquí solo se guarda el registro con su ruta/URL resultante.
router.post('/', auth, (req, res) => {
  const { obra_id, nombre, categoria, url_archivo, visible_cliente } = req.body;
  if (!obra_id || !nombre || !categoria || !url_archivo) {
    return res.status(400).json({ mensaje: 'Faltan campos requeridos' });
  }

  // Si ya existe un documento con el mismo nombre en la obra, se sube como nueva versión
  db.query(
    'SELECT MAX(version) AS maxVersion FROM documentos WHERE obra_id=? AND nombre=?',
    [obra_id, nombre],
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      const version = (rows[0].maxVersion || 0) + 1;

      db.query(`
        INSERT INTO documentos (obra_id,nombre,categoria,url_archivo,version,visible_cliente,subido_por)
        VALUES (?,?,?,?,?,?,?)`,
        [obra_id, nombre, categoria, url_archivo, version, !!visible_cliente, req.usuario.id],
        (err2, r) => {
          if (err2) return res.status(500).json({ mensaje: 'Error al registrar documento' });
          res.status(201).json({ mensaje: `Documento guardado (v${version})`, id: r.insertId, version });
        }
      );
    }
  );
});

// PATCH /api/documentos/:id/visibilidad  (mostrar/ocultar en portal del cliente)
router.patch('/:id/visibilidad', auth, rol('admin', 'supervisor'), (req, res) => {
  const { visible_cliente } = req.body;
  db.query(
    'UPDATE documentos SET visible_cliente=? WHERE id=?',
    [!!visible_cliente, req.params.id],
    (err, r) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
      res.json({ mensaje: 'Visibilidad actualizada' });
    }
  );
});

// DELETE /api/documentos/:id
router.delete('/:id', auth, rol('admin', 'supervisor'), (req, res) => {
  db.query('DELETE FROM documentos WHERE id=?', [req.params.id], (err, r) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!r.affectedRows) return res.status(404).json({ mensaje: 'No encontrado' });
    res.json({ mensaje: 'Documento eliminado' });
  });
});

module.exports = router;
