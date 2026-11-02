"""Generación de tokens opacos para los códigos QR de las entradas."""

from uuid import uuid4


def generar_token_qr():
    return f"QRCINE-{uuid4().hex}"

