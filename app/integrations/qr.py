"""Generación de códigos QR para las entradas."""
import uuid
"""Generación de tokens opacos para los códigos QR de las entradas."""

from uuid import uuid4


def generar_token_qr():
    return f"QRCINE-{uuid4().hex}"


def generar_codigo_qr() -> str:
    """Genera un código QR único sin datos sensibles, usando UUID."""
    return f"QRCINE-{uuid.uuid4().hex[:8]}"
