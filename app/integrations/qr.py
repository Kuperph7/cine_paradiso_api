"""Generación de códigos QR para las entradas."""
import uuid
from io import BytesIO
from uuid import uuid4

import qrcode


def generar_token_qr():
    """Genera un código único para identificar una entrada."""
    return f"QRCINE-{uuid4().hex}"


def generar_codigo_qr() -> str:
    """Mantiene la función de generación existente."""
    return f"QRCINE-{uuid.uuid4().hex[:8]}"


def generar_imagen_qr_png(codigo_qr: str) -> bytes:
    """Convierte el código de una entrada en una imagen PNG."""
    imagen = qrcode.make(codigo_qr)

    archivo = BytesIO()
    imagen.save(archivo, format="PNG")

    return archivo.getvalue()
