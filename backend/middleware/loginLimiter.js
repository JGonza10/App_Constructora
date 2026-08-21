const rateLimit = require('express-rate-limit');

// Protección básica contra fuerza bruta en endpoints de login:
// máximo 8 intentos por IP cada 15 minutos, por endpoint.
// No distingue si el email existe o no (evita enumeración de usuarios).
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 8,
  standardHeaders: true,
  legacyHeaders: false,
  message: { mensaje: 'Demasiados intentos de inicio de sesión. Intenta de nuevo en unos minutos.' },
});

module.exports = loginLimiter;
