"""Envio de alertas (sobrepresupuesto, pagos vencidos) por email y/o Telegram.

Sigue el mismo patron que el resto de los proyectos de Gonza: si no hay
configuracion (variables de entorno vacias), la alerta se registra en el
logger en vez de fallar o tumbar la peticion que la disparo. Nunca lanza
una excepcion hacia quien la llama.
"""
import logging
import os
import smtplib
from email.mime.text import MIMEText

import requests

logger = logging.getLogger("constructora.notificaciones")


def _enviar_email(asunto, cuerpo, destino=None):
    host = os.environ.get("ALERTAS_SMTP_HOST")
    destino = destino or os.environ.get("ALERTAS_EMAIL_DESTINO")
    if not host or not destino:
        return False
    puerto = int(os.environ.get("ALERTAS_SMTP_PORT", "587"))
    usuario = os.environ.get("ALERTAS_SMTP_USER")
    password = os.environ.get("ALERTAS_SMTP_PASSWORD")
    remitente = os.environ.get("ALERTAS_SMTP_FROM", usuario or "alertas@constructora.local")

    msg = MIMEText(cuerpo, "plain", "utf-8")
    msg["Subject"] = asunto
    msg["From"] = remitente
    msg["To"] = destino

    with smtplib.SMTP(host, puerto, timeout=10) as server:
        server.starttls()
        if usuario and password:
            server.login(usuario, password)
        server.sendmail(remitente, [destino], msg.as_string())
    return True


def _enviar_telegram(texto):
    token = os.environ.get("ALERTAS_TELEGRAM_TOKEN")
    chat_id = os.environ.get("ALERTAS_TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": texto}, timeout=10)
    resp.raise_for_status()
    return True


def notificar(asunto, cuerpo):
    """Manda la alerta interna (sobrepresupuesto, pagos vencidos, vencimiento
    de documentos) por todos los canales configurados. Si ninguno esta
    configurado, solo la deja en el log — nunca interrumpe al que la llama."""
    enviado_por_algun_canal = False
    try:
        if _enviar_email(asunto, cuerpo):
            enviado_por_algun_canal = True
    except Exception:
        logger.exception("Fallo al enviar alerta por email: %s", asunto)

    try:
        if _enviar_telegram(f"*{asunto}*\n{cuerpo}"):
            enviado_por_algun_canal = True
    except Exception:
        logger.exception("Fallo al enviar alerta por Telegram: %s", asunto)

    if not enviado_por_algun_canal:
        logger.warning("[ALERTA sin canal configurado] %s — %s", asunto, cuerpo)


def notificar_cliente(email_destino, asunto, cuerpo):
    """Avisa a un cliente puntual (avance nuevo, documento nuevo visible) por
    su propio correo — a diferencia de notificar(), que va a los canales fijos
    del equipo interno. Sin SMTP configurado, tambien degrada al log."""
    if not email_destino:
        return
    try:
        if not _enviar_email(asunto, cuerpo, destino=email_destino):
            logger.warning("[AVISO A CLIENTE sin SMTP configurado] %s <- %s: %s", email_destino, asunto, cuerpo)
    except Exception:
        logger.exception("Fallo al notificar al cliente %s: %s", email_destino, asunto)
