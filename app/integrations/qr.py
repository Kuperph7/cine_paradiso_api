"""Generación de códigos QR para las entradas."""
import uuid


def generar_codigo_qr() -> str:
    """Genera un código QR único sin datos sensibles, usando UUID."""
    return f"QRCINE-{uuid.uuid4().hex[:8]}"
