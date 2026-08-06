const mysql = require('mysql2');

// Soporta tanto variables locales (DB_*) como las que genera Railway (MYSQL*)
const dbPassword = process.env.DB_PASSWORD || process.env.MYSQLPASSWORD;
if (!dbPassword) {
  throw new Error(
    'Falta configurar DB_PASSWORD (o MYSQLPASSWORD) en las variables de entorno. ' +
    'Copia backend/.env.example a backend/.env y define una contraseña real antes de iniciar el servidor.'
  );
}

const db = mysql.createConnection({
  host:     process.env.DB_HOST     || process.env.MYSQLHOST     || 'localhost',
  user:     process.env.DB_USER     || process.env.MYSQLUSER     || 'root',
  password: dbPassword,
  database: process.env.DB_NAME     || process.env.MYSQLDATABASE || 'constructora',
  port:     process.env.DB_PORT     || process.env.MYSQLPORT     || 3306
});

db.connect(err => {
  if (err) {
    console.error('Error al conectar con MySQL:', err.message);
    process.exit(1);
  }
  console.log('✅ Conectado a la base de datos MySQL');
});

module.exports = db;
