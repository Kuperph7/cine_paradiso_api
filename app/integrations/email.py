"""Envío de comprobantes, entradas por correo electrónico y confirmacion de usuario."""

import os
import smtplib
from email.message import EmailMessage
from app.integrations.qr import generar_imagen_qr_png
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def enviar_correo_compra(conn, compra_id):
    """Consulta los detalles de la compra usando SQL puro y envía el recibo por email."""
    cursor = conn.cursor(dictionary=True)

    try:
        # Consultar datos generales de la compra, cliente, película y sala
        query_general = """
            SELECT 
                usuarios.nombre AS cliente_nombre,
                usuarios.email AS cliente_email,
                compras.id AS compra_id,
                compras.medio_pago,
                compras.total_entradas,
                compras.total_servicios,
                compras.total,
                peliculas.titulo AS pelicula,
                funciones.fecha_hora AS fecha_funcion,
                salas.nombre AS sala,
                locales.nombre AS local_nombre
            FROM compras
            JOIN usuarios ON compras.usuario_id = usuarios.id
            JOIN funciones ON compras.funcion_id = funciones.id
            JOIN peliculas ON funciones.pelicula_id = peliculas.id
            JOIN salas ON funciones.sala_id = salas.id
            JOIN locales ON salas.local_id = locales.id
            WHERE compras.id = %s
        """
        cursor.execute(query_general, (compra_id,))
        datos_compra = cursor.fetchone()

        if not datos_compra:
            return

        #Consultar las butacas compradas (solo fila y número para el recibo)
        query_butacas = """
            SELECT butacas.fila, butacas.numero
            FROM entradas
            JOIN butacas_funcion ON entradas.butaca_funcion_id = butacas_funcion.id
            JOIN butacas ON butacas_funcion.butaca_id = butacas.id
            WHERE entradas.compra_id = %s
        """
        cursor.execute(query_butacas, (compra_id,))
        butacas = cursor.fetchall()

        #Consultar los combos/servicios adicionales (si los hay)
        query_servicios = """
            SELECT servicios.nombre, compras_servicios.cantidad, compras_servicios.subtotal
            FROM compras_servicios
            JOIN servicios ON compras_servicios.servicio_id = servicios.id
            WHERE compras_servicios.compra_id = %s
        """
        cursor.execute(query_servicios, (compra_id,))
        servicios = cursor.fetchall()

    finally:
        cursor.close()

    #Armar lista de butacas y combos en texto/HTML para el recibo
    lista_butacas = ", ".join(
        f"Fila {b['fila']} - Asiento {b['numero']}" for b in butacas
    )

    servicios_html = ""
    if servicios:
        items = "".join(
            f"<li>{s['cantidad']}x {s['nombre']} (${s['subtotal']})</li>"
            for s in servicios
        )
        servicios_html = f"""
        <div style="text-align: left; margin-top: 12px;">
            <p style="margin: 0 0 4px 0; font-weight: bold;">Servicios / Candy Bar:</p>
            <ul style="margin: 0; padding-left: 20px;">{items}</ul>
        </div>
        """

    #Cuerpo completo del recibo en HTML
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; text-align: center; color: #102044;">
        <h2>¡Muchas gracias por tu compra, {datos_compra['cliente_nombre']}!</h2>
        <p>Tu pago fue confirmado con éxito. Acá tenés el recibo con el detalle de tu operación:</p>
        
        <div style="background-color: #f7d369; border-radius: 20px; padding: 24px; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0;">{datos_compra['pelicula']}</h3>
            <p style="margin: 4px 0;"><strong>Cine:</strong> {datos_compra['local_nombre']} - {datos_compra['sala']}</p>
            <p style="margin: 4px 0;"><strong>Fecha y hora:</strong> {datos_compra['fecha_funcion']}</p>
            <p style="margin: 4px 0;"><strong>Butacas:</strong> {lista_butacas}</p>
            <p style="margin: 4px 0;"><strong>Medio de pago:</strong> {datos_compra['medio_pago']}</p>
            
            {servicios_html}
            
            <hr style="border: none; border-top: 1px solid #102044; margin: 16px 0;">
            <p style="margin: 4px 0;">Subtotal entradas: ${datos_compra['total_entradas']}</p>
            <p style="margin: 4px 0;">Subtotal servicios: ${datos_compra['total_servicios']}</p>
            <p style="font-size: 20px; font-weight: bold; margin: 12px 0 0 0;">Total pagado: ${datos_compra['total']}</p>
        </div>
        
        <p style="font-size: 12px; color: #555;">Recibo de compra #{datos_compra['compra_id']} - Cine Paradiso</p>
    </div>
    """

    #Configurar y enviar el correo por SMTP (Gmail)
    remitente = os.getenv("MAIL_USER")
    password_app = os.getenv("MAIL_PASSWORD")

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = f"Recibo de compra #{datos_compra['compra_id']} - {datos_compra['pelicula']}"
    mensaje["From"] = remitente
    mensaje["To"] = datos_compra["cliente_email"]
    mensaje.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(remitente, password_app)
        server.send_message(mensaje)