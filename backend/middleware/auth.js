const jwt = require('jsonwebtoken');

if (!process.env.JWT_SECRET) {
  throw new Error(
    'Falta configurar JWT_SECRET en las variables de entorno. ' +
    'Copia backend/.env.example a backend/.env y define un secreto propio antes de iniciar el servidor.'
  );
}
const SECRET = process.env.JWT_SECRET;

function verificarToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ')
    ? authHeader.slice(7)
    : authHeader;

  if (!token) {
    return res.status(403).json({ mensaje: 'Token requerido' });
  }

  jwt.verify(token, SECRET, (err, decoded) => {
    if (err) return res.status(401).json({ mensaje: 'Token inválido o expirado' });
    req.usuario = decoded;
    next();
  });
}

module.exports = verificarToken;
