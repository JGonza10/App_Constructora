require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const http = require('http');
const socketIo = require('socket.io');

const usuarios = require('./routes/usuarios');
const presupuestos = require('./routes/presupuestos');
const admin = require('./routes/admin');
const clientes = require('./routes/clientes');
const obras = require('./routes/obras');
const gastos = require('./routes/gastos');
const avance = require('./routes/avance');
const pagos = require('./routes/pagos');
const proveedores = require('./routes/proveedores');
const tareas = require('./routes/tareas');
const bitacora = require('./routes/bitacora');
const tablero = require('./routes/tablero');
const estimaciones = require('./routes/estimaciones');
const documentos = require('./routes/documentos');
const portal = require('./routes/portal');

const app = express();
const server = http.createServer(app);

const io = socketIo(server, {
  cors: { origin: process.env.FRONTEND_URL || '*', methods: ['GET', 'POST'] }
});

// Middlewares globales
app.use(helmet()); // cabeceras de seguridad (HSTS, X-Content-Type-Options, etc.)
app.use(cors({ origin: process.env.FRONTEND_URL || '*' }));
app.use(express.json());

// Pasar io a las rutas (para emitir eventos en tiempo real)
app.use((req, _res, next) => { req.io = io; next(); });

// Rutas API
app.use('/api/usuarios', usuarios);
app.use('/api/presupuestos', presupuestos);
app.use('/api/admin', admin);
app.use('/api/clientes', clientes);
app.use('/api/obras', obras);
app.use('/api/gastos', gastos);
app.use('/api/avance', avance);
app.use('/api/pagos', pagos);
app.use('/api/proveedores', proveedores);
app.use('/api/tareas', tareas);
app.use('/api/bitacora', bitacora);
app.use('/api/tablero', tablero);
app.use('/api/estimaciones', estimaciones);
app.use('/api/documentos', documentos);
app.use('/api/portal', portal);

// Ruta de salud
app.get('/api/health', (_req, res) => res.json({ status: 'ok', timestamp: new Date() }));

// Socket.io — eventos en tiempo real
io.on('connection', (socket) => {
  console.log(`🔌 Cliente conectado: ${socket.id}`);

  socket.on('unirse_sala', (rol) => {
    socket.join(rol);
    console.log(`Usuario unido a sala: ${rol}`);
  });

  socket.on('nueva_alerta', (data) => {
    io.emit('alerta_recibida', data);
  });

  socket.on('presupuesto_actualizado', (data) => {
    io.emit('presupuesto_cambio', data);
  });

  socket.on('obra_actualizada', (data) => {
    io.emit('obra_cambio', data);
  });

  socket.on('gasto_registrado', (data) => {
    io.emit('gasto_nuevo', data);
  });

  socket.on('disconnect', () => {
    console.log(`❌ Cliente desconectado: ${socket.id}`);
  });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`🚀 Servidor corriendo en http://localhost:${PORT}`);
});
