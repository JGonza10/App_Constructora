import bcrypt

usuarios = [
    (1, "Admin123!"),
    (2, "Super123!"),
    (3, "Empl123!")
]

print("Ejecuta estas líneas en phpMyAdmin > pestaña SQL:\n")
for uid, pwd in usuarios:
    h = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt(10)).decode()
    print(f"UPDATE usuarios SET password='{h}' WHERE id={uid};")