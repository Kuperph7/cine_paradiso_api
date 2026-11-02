"""Consultas SQL relacionadas con entradas."""
from datetime import datetime, timezone
from app.db import get_db_connection


def obtener_entradas_por_cliente(usuario_id: int) -> list:
    """Devuelve todas las entradas del cliente autenticado con datos de función y butaca."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT
                e.id, e.compra_id, e.funcion_id, e.butaca_id,
                e.precio, e.codigo_qr, e.estado
            FROM entradas e
            JOIN compras c ON c.id = e.compra_id
            WHERE c.usuario_id = %s
            ORDER BY e.id DESC
        """
        cursor.execute(query, (usuario_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_entrada_por_id(entrada_id: int, usuario_id: int):
    """Busca una entrada específica verificando que pertenezca al cliente autenticado."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT
                e.id, e.compra_id, e.funcion_id, e.butaca_id,
                e.precio, e.codigo_qr, e.estado
            FROM entradas e
            JOIN compras c ON c.id = e.compra_id
            WHERE e.id = %s AND c.usuario_id = %s
        """
        cursor.execute(query, (entrada_id, usuario_id))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def obtener_entrada_por_qr(codigo_qr: str, funcion_id: int):
    """Busca una entrada por su código QR y función para el control de acceso."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, compra_id, funcion_id, butaca_id,
                   precio, codigo_qr, estado
            FROM entradas
            WHERE codigo_qr = %s AND funcion_id = %s
        """
        cursor.execute(query, (codigo_qr, funcion_id))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def marcar_entrada_utilizada(entrada_id: int) -> int:
    """Actualiza el estado a 'utilizada' y registra la fecha de validación de forma atómica."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        ahora = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        query = """
            UPDATE entradas
            SET estado = 'utilizada', fecha_hora_validacion = %s
            WHERE id = %s AND estado = 'emitida'
        """
        cursor.execute(query, (ahora, entrada_id))
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()
