const mysql = require('mysql2');

// Soporta tanto variables locales (DB_*) como las que genera Railway (MYSQL*)
const db = mysql.createConnection({
  host:     process.env.DB_HOST     || process.env.MYSQLHOST     || 'localhost',
  user:     process.env.DB_USER     || process.env.MYSQLUSER     || 'root',
  password: process.env.DB_PASSWORD || process.env.MYSQLPASSWORD || 'TU_PASSWORD',
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
