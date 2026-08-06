#!/usr/bin/env python3
"""
Script para generar los hash bcrypt reales de las contraseñas de ejemplo.
Corre este script ANTES de importar el SQL, y reemplaza los placeholders.

Uso:
  pip install bcrypt
  python3 generar_hashes.py
"""
import bcrypt

usuarios = [
    ("admin@constructora.com",    "Admin123!"),
    ("supervisor@constructora.com", "Super123!"),
    ("empleado@constructora.com",  "Empl123!"),
]

print("-- Copia estas líneas al archivo constructora.sql (reemplaza los INSERT de usuarios)\n")
print("INSERT INTO usuarios (nombre, email, password, rol) VALUES")
filas = []
nombres_roles = [
    ("Carlos Admin", "admin"),
    ("Laura Supervisora", "supervisor"),
    ("Miguel Empleado", "empleado"),
]
for (email, pwd), (nombre, rol) in zip(usuarios, nombres_roles):
    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(10)).decode()
    filas.append(f"  ('{nombre}', '{email}', '{hashed}', '{rol}')")

print(",\n".join(filas) + ";")
print(f"\n-- Contraseñas originales (solo para pruebas):")
for email, pwd in usuarios:
    print(f"--   {email}: {pwd}")
