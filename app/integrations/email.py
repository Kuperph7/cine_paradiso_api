"""Envío de comprobantes y entradas por correo electrónico."""

import os
import smtplib
from email.message import EmailMessage

from app.integrations.qr import generar_imagen_qr_png


def enviar_entradas_por_email(destinatario, compra):
    """Envía las entradas de una compra con sus QR adjuntos."""

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "1025"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    remitente = os.getenv("SMTP_FROM")

    if not smtp_host or not remitente:
        return False

    mensaje = EmailMessage()
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje["Subject"] = f"Cine Paradiso - Compra #{compra['id']}"


    texto = (
        "¡Gracias por comprar en Cine Paradiso!\n\n"
        f"Compra #{compra['id']}\n"
        "Adjuntamos los códigos QR de tus entradas.\n\n"
    )

    for entrada in compra["entradas"]:
        butaca = entrada["butaca"]
        codigo = entrada["codigo_qr"]

        texto += (
            f"Butaca {butaca['fila']}{butaca['numero']}\n"
            f"Código: {codigo}\n\n"
        )

    mensaje.set_content(texto)

    for entrada in compra["entradas"]:
        imagen = generar_imagen_qr_png(entrada["codigo_qr"])

        mensaje.add_attachment(
            imagen,
            maintype="image",
            subtype="png",
            filename=f"entrada-{entrada['id']}.png",
        )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as servidor:
        if os.getenv("SMTP_STARTTLS", "false").lower() == "true":
            servidor.starttls()

        if smtp_user and smtp_password:
            servidor.login(smtp_user, smtp_password)

        servidor.send_message(mensaje)

    return True

