import bcrypt

usuarios = [
    (1, "Direccion#2026"),
    (2, "Supervisa#2026"),
    (3, "Campo#2026")
]

print("Ejecuta estas líneas en phpMyAdmin > pestaña SQL:\n")
for uid, pwd in usuarios:
    h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(10)).decode()
    print(f"UPDATE usuarios SET password='{h}' WHERE id={uid};")