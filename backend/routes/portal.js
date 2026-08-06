const express = require('express');
const router  = express.Router();
const bcrypt  = require('bcrypt');
const jwt     = require('jsonwebtoken');
const db      = require('../db');

if (!process.env.JWT_SECRET) {
  throw new Error(
    'Falta configurar JWT_SECRET en las variables de entorno. ' +
    'Copia backend/.env.example a backend/.env y define un secreto propio antes de iniciar el servidor.'
  );
}
const SECRET = process.env.JWT_SECRET;

// Middleware propio: verifica token de tipo "cliente"
function verificarClienteToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
  if (!token) return res.status(403).json({ mensaje: 'Token requerido' });

  jwt.verify(token, SECRET, (err, decoded) => {
    if (err || decoded.tipo !== 'cliente') {
      return res.status(401).json({ mensaje: 'Token inválido o expirado' });
    }
    req.clienteAuth = decoded;
    next();
  });
}

// POST /api/portal/login  (login exclusivo de clientes)
router.post('/login', (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ mensaje: 'Email y password requeridos' });

  db.query(
    `SELECT ca.*, c.nombre AS cliente_nombre
     FROM clientes_acceso ca JOIN clientes c ON c.id = ca.cliente_id
     WHERE ca.email = ? AND ca.activo = TRUE`,
    [email],
    async (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (!rows.length) return res.status(401).json({ mensaje: 'Credenciales inválidas' });

      const acceso = rows[0];
      const coincide = await bcrypt.compare(password, acceso.password);
      if (!coincide) return res.status(401).json({ mensaje: 'Credenciales inválidas' });

      const token = jwt.sign(
        { tipo: 'cliente', cliente_id: acceso.cliente_id, nombre: acceso.cliente_nombre, email: acceso.email },
        SECRET, { expiresIn: '8h' }
      );
      res.json({ token, cliente: { id: acceso.cliente_id, nombre: acceso.cliente_nombre, email: acceso.email } });
    }
  );
});

// GET /api/portal/obras  (solo las obras del cliente autenticado)
router.get('/obras', verificarClienteToken, (req, res) => {
  db.query(`
    SELECT o.id, o.nombre, o.tipo, o.estado, o.avance_porcentaje,
           o.monto_contrato, o.fecha_inicio, o.fecha_fin_estimada, o.direccion
    FROM obras o
    WHERE o.cliente_id = ?
    ORDER BY o.fecha_inicio DESC`,
    [req.clienteAuth.cliente_id],
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error al obtener obras' });
      res.json(rows);
    }
  );
});

// GET /api/portal/obras/:id  (detalle — valida que la obra sea del cliente)
router.get('/obras/:id', verificarClienteToken, (req, res) => {
  db.query(`
    SELECT o.id, o.nombre, o.tipo, o.estado, o.avance_porcentaje,
           o.monto_contrato, o.fecha_inicio, o.fecha_fin_estimada, o.direccion, o.descripcion
    FROM obras o
    WHERE o.id = ? AND o.cliente_id = ?`,
    [req.params.id, req.clienteAuth.cliente_id],
    (err, rows) => {
      if (err) return res.status(500).json({ mensaje: 'Error interno' });
      if (!rows.length) return res.status(404).json({ mensaje: 'Obra no encontrada' });
      res.json(rows[0]);
    }
  );
});

// GET /api/portal/obras/:id/avance  (avance de la obra, solo lectura)
router.get('/obras/:id/avance', verificarClienteToken, (req, res) => {
  // Verifica pertenencia antes de mostrar datos
  db.query('SELECT id FROM obras WHERE id=? AND cliente_id=?', [req.params.id, req.clienteAuth.cliente_id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!rows.length) return res.status(403).json({ mensaje: 'Acceso denegado' });

    db.query(
      'SELECT semana, etapa, porcentaje, descripcion FROM avance_obra WHERE obra_id=? ORDER BY semana DESC',
      [req.params.id],
      (err2, avances) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al obtener avance' });
        res.json(avances);
      }
    );
  });
});

// GET /api/portal/obras/:id/pagos  (estado de cuenta del cliente)
router.get('/obras/:id/pagos', verificarClienteToken, (req, res) => {
  db.query('SELECT id FROM obras WHERE id=? AND cliente_id=?', [req.params.id, req.clienteAuth.cliente_id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!rows.length) return res.status(403).json({ mensaje: 'Acceso denegado' });

    db.query(
      'SELECT concepto, monto, fecha_programada, fecha_recibido, estado FROM pagos_cliente WHERE obra_id=? ORDER BY fecha_programada',
      [req.params.id],
      (err2, pagos) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al obtener pagos' });
        res.json(pagos);
      }
    );
  });
});

// GET /api/portal/obras/:id/documentos  (solo documentos marcados como visibles)
router.get('/obras/:id/documentos', verificarClienteToken, (req, res) => {
  db.query('SELECT id FROM obras WHERE id=? AND cliente_id=?', [req.params.id, req.clienteAuth.cliente_id], (err, rows) => {
    if (err) return res.status(500).json({ mensaje: 'Error interno' });
    if (!rows.length) return res.status(403).json({ mensaje: 'Acceso denegado' });

    db.query(
      `SELECT id, nombre, categoria, url_archivo, version, creado_en
       FROM documentos WHERE obra_id=? AND visible_cliente=TRUE ORDER BY categoria`,
      [req.params.id],
      (err2, docs) => {
        if (err2) return res.status(500).json({ mensaje: 'Error al obtener documentos' });
        res.json(docs);
      }
    );
  });
});

module.exports = router;
