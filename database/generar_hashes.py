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
    ("ana.ramirez@constructora.com",      "Direccion#2026"),
    ("jorge.villasenor@constructora.com", "Supervisa#2026"),
    ("paola.reyes@constructora.com",      "Campo#2026"),
]

print("-- Copia estas líneas al archivo constructora.sql (reemplaza los INSERT de usuarios)\n")
print("INSERT INTO usuarios (nombre, email, password, rol) VALUES")
filas = []
nombres_roles = [
    ("Ana Ramírez", "admin"),
    ("Jorge Villaseñor", "supervisor"),
    ("Paola Reyes", "empleado"),
]
for (email, pwd), (nombre, rol) in zip(usuarios, nombres_roles):
    hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(10)).decode()
    filas.append(f"  ('{nombre}', '{email}', '{hashed}', '{rol}')")

print(",\n".join(filas) + ";")
print(f"\n-- Contraseñas originales (solo para pruebas):")
for email, pwd in usuarios:
    print(f"--   {email}: {pwd}")
