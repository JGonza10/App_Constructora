"""Subida de archivos reales a disco (documentos de obra, fotos de bitacora).

Convencion: una ruta que empieza con 'local:' apunta a un archivo guardado en
`instance/uploads/...` y se sirve por una ruta protegida de la app; cualquier
otro valor se trata como URL externa y se usa tal cual (mismo patron que
`local:<archivo>` en Chicos Wheels/CollectHub, para no inventar uno nuevo)."""
import os
import uuid

from flask import current_app

EXTENSIONES_PERMITIDAS = {
    "pdf", "png", "jpg", "jpeg", "webp", "gif", "doc", "docx", "xls", "xlsx", "dwg",
}


def guardar_archivo(file_storage, subcarpeta):
    """Guarda un FileStorage de Flask-WTF bajo instance/uploads/<subcarpeta>/
    con un nombre aleatorio (nunca el nombre original, para no depender de
    el ni exponerlo) y devuelve la referencia 'local:<ruta relativa>'."""
    extension = file_storage.filename.rsplit(".", 1)[1].lower()
    nombre_guardado = f"{uuid.uuid4().hex}.{extension}"
    carpeta_absoluta = os.path.join(current_app.instance_path, "uploads", subcarpeta)
    os.makedirs(carpeta_absoluta, exist_ok=True)
    ruta_absoluta = os.path.join(carpeta_absoluta, nombre_guardado)
    file_storage.save(ruta_absoluta)
    ruta_relativa = f"{subcarpeta}/{nombre_guardado}"
    return f"local:{ruta_relativa}"


def guardar_bytes(contenido, extension, subcarpeta):
    """Como guardar_archivo, pero para contenido que no llego como FileStorage
    (ej. una firma capturada en un <canvas> y mandada como base64)."""
    nombre_guardado = f"{uuid.uuid4().hex}.{extension}"
    carpeta_absoluta = os.path.join(current_app.instance_path, "uploads", subcarpeta)
    os.makedirs(carpeta_absoluta, exist_ok=True)
    ruta_absoluta = os.path.join(carpeta_absoluta, nombre_guardado)
    with open(ruta_absoluta, "wb") as f:
        f.write(contenido)
    return f"local:{subcarpeta}/{nombre_guardado}"


def ruta_absoluta_de(referencia_local):
    """referencia_local es lo guardado en BD, ej. 'local:documentos/obra_3/xxx.pdf'."""
    ruta_relativa = referencia_local.removeprefix("local:")
    return os.path.join(current_app.instance_path, "uploads", ruta_relativa)


def es_local(referencia):
    return bool(referencia) and referencia.startswith("local:")
