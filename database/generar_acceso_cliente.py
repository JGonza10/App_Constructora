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
print(f"\n-- Datos de acceso para el cliente (URL del portal + email + contraseña temporal):")
print(f"--   URL del portal: https://tu-dominio.com/portal/login")
print(f"--   Email: {email}")
print(f"--   Contraseña temporal: {password}")
print(
    "\n-- IMPORTANTE (seguridad): no pegues esta contraseña en un correo o chat "
    "en texto plano ni la dejes en el historial de la terminal.\n"
    "-- Entrégala en persona, por llamada telefónica, o por un canal que el "
    "cliente ya usa y controla (WhatsApp donde ya lo conoces, verbalmente, etc.),\n"
    "-- y trátala como temporal: la tabla clientes_acceso no tiene todavía un "
    "flujo de 'cambiar contraseña', así que documenta con el cliente que esta\n"
    "-- es la que va a usar de forma permanente hasta que se implemente ese flujo."
)
