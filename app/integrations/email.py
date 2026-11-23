"""Envío de comprobantes, entradas por correo electrónico y confirmacion de usuario."""

import os
import smtplib
from email.message import EmailMessage
from app.integrations.qr import generar_imagen_qr_png
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

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

    entradas_html = ""
    
    for entrada in compra["entradas"]:
        butaca = entrada["butaca"]
        codigo = entrada["codigo_qr"]

        texto += (
            f"Butaca {butaca['fila']}{butaca['numero']}\n"
            f"Código: {codigo}\n\n"
        )

        entradas_html += f"""
        <div style="background-color: #ffffff; border-radius: 12px; padding: 14px; margin: 12px 0; text-align: left;">
            <p style="margin: 0 0 4px 0; font-size: 16px; font-weight: bold; color: #102044;">
                Butaca {butaca['fila']}{butaca['numero']}
            </p>
            <p style="margin: 0; font-size: 13px; color: #333; word-break: break-all;">
                <strong>Código QR:</strong> {codigo}
            </p>
        </div>
        """
    html = f"""
    <div style="background-color: #a7bac8; padding: 30px 15px; width: 100%; box-sizing: border-box;">
        <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; text-align: center; color: #102044;">
            <h2>¡Gracias por comprar en Cine Paradiso!</h2>
            <p>Tu compra <strong>#{compra['id']}</strong> está lista. Adjuntamos los códigos QR de tus entradas en este correo:</p>
            
            <div style="background-color: #f7d369; border-radius: 20px; padding: 24px; margin: 20px 0;">
                <h3 style="margin: 0 0 12px 0;">Tus Entradas ({len(compra['entradas'])})</h3>
                {entradas_html}
            </div>
            
            <p style="font-size: 12px; color: #333;">Presentá los códigos QR adjuntos al ingresar a la sala - Cine Paradiso</p>
        </div>
    </div>
    """
    mensaje.set_content(texto)
    mensaje.add_alternative(html, subtype="html")

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
    cantidad_entradas = len(butacas)
    lista_butacas = ", ".join(
        f"Fila {b['fila']} - Asiento {b['numero']}" for b in butacas
    )

    # Calcular fecha límite de cancelación 24 horas antes de la función
    fecha_funcion = datos_compra['fecha_funcion']
    if isinstance(fecha_funcion, str):
        fecha_funcion = datetime.strptime(fecha_funcion, "%Y-%m-%d %H:%M:%S")
    
    fecha_limite = (fecha_funcion - timedelta(hours=24)).strftime("%d/%m/%Y %H:%M")
    
    # URL hacia la pantalla de detalle/cancelación en tu Frontend (ajustá el puerto/dominio si hace falta)
    frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5000")
    url_cancelar = f"{frontend_url}/entradas/{datos_compra['compra_id']}"

    servicios_html = ""
    if servicios:
        items = "".join(
            f"<li>{s['cantidad']}x {s['nombre']} (${s['subtotal']})</li>"
            for s in servicios
        )
        servicios_html = f"""
        <div style="text-align: left; margin-top: 12px;">
            <p style="margin: 0 0 4px 0; font-weight: bold;">Candy Bar:</p>
            <ul style="margin: 0; padding-left: 20px;">{items}</ul>
        </div>
        """

    #Cuerpo completo del recibo en HTML

    html = f"""
    <div style="background-color: #a7bac8; padding: 30px 15px; width: 100%; box-sizing: border-box;">
        <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; text-align: center; color: #102044;">
            <h2>¡Muchas gracias por tu compra, {datos_compra['cliente_nombre']}!</h2>
            <p>Tu pago fue confirmado con éxito. Acá tenés el recibo con el detalle de tu operación:</p>
            
            <div style="background-color: #f7d369; border-radius: 20px; padding: 24px; margin: 20px 0;">
                <h3 style="margin: 0 0 10px 0;">{datos_compra['pelicula']}</h3>
                <p style="margin: 4px 0;"><strong>Cine:</strong> {datos_compra['local_nombre']} - {datos_compra['sala']}</p>
                <p style="margin: 4px 0;"><strong>Fecha y hora:</strong> {datos_compra['fecha_funcion']}</p>
                <p style="margin: 4px 0;"><strong>Entradas ({cantidad_entradas}):</strong> {lista_butacas}</p>
                <p style="margin: 4px 0;"><strong>Medio de pago:</strong> {datos_compra['medio_pago']}</p>
                
                {servicios_html}
                
                <hr style="border: none; border-top: 1px solid #102044; margin: 16px 0;">
                <p style="margin: 4px 0;">Subtotal entradas: ${datos_compra['total_entradas']}</p>
                <p style="margin: 4px 0;">Subtotal servicios: ${datos_compra['total_servicios']}</p>
                <p style="font-size: 20px; font-weight: bold; margin: 12px 0 0 0;">Total pagado: ${datos_compra['total']}</p>
            </div>

            <div style="margin: 20px 0;">
                <a href="{url_cancelar}" style="display: inline-block; background-color: #f7d369; color: #102044; border: 2px solid #102044; padding: 12px 28px; border-radius: 999px; font-weight: bold; font-size: 14px; text-decoration: none;">
                    Gestionar o cancelar compra
                </a>
            </div>

            <p style="font-size: 12px; color: #102044; max-width: 420px; margin: 0 auto 14px auto; line-height: 1.4;">
                Tenés tiempo hasta el <strong>{fecha_limite} hs</strong> (24 hs antes de la función) para solicitar la cancelación; pasado ese plazo, no se realizan reembolsos.
            </p>
            
            <p style="font-size: 12px; color: #333;">Recibo de compra #{datos_compra['compra_id']} - Cine Paradiso</p>
        </div>
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

def _enviar_mensaje_html(destinatario, asunto, html):
    """Envía un correo HTML usando la configuración SMTP del proyecto o Gmail."""
    smtp_host = os.getenv("SMTP_HOST", "127.0.0.1")
    smtp_port = int(os.getenv("SMTP_PORT", "1025"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    mail_user = os.getenv("MAIL_USER")
    mail_password = os.getenv("MAIL_PASSWORD")
    remitente = (
        os.getenv("SMTP_FROM")
        or mail_user
        or "entradas@cineparadiso.local"
    )

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destinatario
    mensaje.attach(MIMEText(html, "html"))

    if mail_user and mail_password and not os.getenv("SMTP_HOST"):
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(mail_user, mail_password)
            server.send_message(mensaje)
        return True

    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as servidor:
        if os.getenv("SMTP_STARTTLS", "false").lower() == "true":
            servidor.starttls()
        if smtp_user and smtp_password:
            servidor.login(smtp_user, smtp_password)
        servidor.send_message(mensaje)
    return True


def enviar_correo_registro(destinatario, nombre_usuario):
    """Envía un correo electrónico de confirmación cuando un usuario se registra con éxito."""
    html = f"""
    <div style="background-color: #a7bac8 ; padding: 30px 15px; width: 100%; box-sizing: border-box;">
        <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; text-align: center; color: #102044;">
            <h2>¡Bienvenido/a a Cine Paradiso, {nombre_usuario}!</h2>
            
            <div style="background-color: #f7d369; border-radius: 20px; padding: 24px; margin: 20px 0;">
                <p style="font-size: 16px; margin: 0 0 12px 0;">
                    Tu cuenta fue creada correctamente con el correo <strong>{destinatario}</strong>.
                </p>
                <p style="font-size: 15px; margin: 0;">
                    Ya podés iniciar sesión, explorar nuestra cartelera, elegir tus butacas y reservar combos para tus próximas funciones.
                </p>
            </div>
            
            <p style="font-size: 12px; color: #555;">Equipo de Cine Paradiso</p>
        </div>
    </div>
    """
    return _enviar_mensaje_html(
        destinatario,
        "¡Registro exitoso! Bienvenido/a a Cine Paradiso",
        html,
    )


def enviar_correo_recuperacion_password(
    destinatario,
    nombre_usuario,
    token_recuperacion,
):
    """Envía un correo con el enlace y código para restablecer la contraseña."""
    frontend_url = os.getenv("FRONTEND_PUBLIC_URL", "http://localhost:8080").rstrip("/")
    enlace = f"{frontend_url}/recuperar-password?token={token_recuperacion}"

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 550px; margin: 0 auto; text-align: center; color: #102044;">
        <h2>Hola, {nombre_usuario}</h2>
        <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en Cine Paradiso.</p>

        <div style="background-color: #f7d369; border-radius: 20px; padding: 24px; margin: 20px 0;">
            <p style="font-size: 15px; margin: 0 0 16px 0;">
                Hacé clic en el siguiente botón para elegir tu nueva contraseña (válido por 30 minutos):
            </p>
            <p style="margin: 16px 0;">
                <a href="{enlace}" style="background-color: #102044; color: #ffffff; padding: 12px 24px; border-radius: 999px; text-decoration: none; font-weight: bold; display: inline-block;">
                    Restablecer mi contraseña
                </a>
            </p>
            <p style="font-size: 13px; margin: 16px 0 4px 0;">
                O copiá y pegá este código de recuperación en la pantalla de inicio de sesión:
            </p>
            <p style="font-family: monospace; font-size: 12px; word-break: break-all; background: #ffffff; padding: 10px; border-radius: 8px; margin: 0;">
                {token_recuperacion}
            </p>
        </div>

        <p style="font-size: 12px; color: #555;">Si no solicitaste este cambio, podés ignorar este correo.</p>
    </div>
    """
    return _enviar_mensaje_html(
        destinatario,
        "Recuperación de contraseña - Cine Paradiso",
        html,
    )