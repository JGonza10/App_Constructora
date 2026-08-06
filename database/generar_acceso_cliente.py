#!/usr/bin/env python3
"""
Genera el hash bcrypt para dar de alta el acceso al Portal del Cliente.
El admin/supervisor ejecuta esto para crear las credenciales de un cliente,
y luego inserta el resultado en la tabla `clientes_acceso`.

Uso:
  pip install bcrypt
  python3 generar_acceso_cliente.py
"""
import bcrypt

print("=== Generador de acceso al Portal del Cliente ===\n")
cliente_id = input("ID del cliente (ver tabla 'clientes'): ").strip()
email = input("Email de acceso: ").strip()
password = input("Contraseña temporal: ").strip()

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10)).decode()

print("\n-- Ejecuta este INSERT en MySQL:\n")
print(f"INSERT INTO clientes_acceso (cliente_id, email, password) VALUES")
print(f"  ({cliente_id}, '{email}', '{hashed}');")
print(f"\n-- Comparte con el cliente:")
print(f"--   URL del portal: http://tu-dominio.com/portal/login")
print(f"--   Email: {email}")
print(f"--   Contraseña: {password}")
