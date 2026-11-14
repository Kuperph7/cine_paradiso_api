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

def crear_entrada(
    conexion,
    compra_id,
    butaca_funcion_id,
    precio,
    codigo_qr,
):
    consulta = """
        INSERT INTO entradas (
            compra_id,
            butaca_funcion_id,
            precio,
            codigo_qr,
            estado
        )
        VALUES (%s, %s, %s, %s, 'vigente')
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(
            consulta,
            (compra_id, butaca_funcion_id, precio, codigo_qr),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def listar_entradas_compra(conexion, compra_id):
    consulta = """
        SELECT
            e.id,
            e.compra_id,
            c.usuario_id,
            c.funcion_id,
            b.id AS butaca_id,
            b.fila,
            b.numero,
            bf.estado AS estado_butaca,
            e.codigo_qr,
            e.estado,
            e.fecha_hora_validacion AS utilizada_en
        FROM entradas AS e
        INNER JOIN compras AS c ON c.id = e.compra_id
        INNER JOIN butacas_funcion AS bf ON bf.id = e.butaca_funcion_id
        INNER JOIN butacas AS b ON b.id = bf.butaca_id
        WHERE e.compra_id = %s
        ORDER BY b.fila, b.numero, e.id
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (compra_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def bloquear_entradas_compra(conexion, compra_id):
    consulta = """
        SELECT id, estado
        FROM entradas
        WHERE compra_id = %s
        ORDER BY id
        FOR UPDATE
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (compra_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def cancelar_entradas_compra(conexion, compra_id):
    consulta = """
        UPDATE entradas
        SET estado = 'cancelada',
            fecha_hora_cancelacion = CURRENT_TIMESTAMP
        WHERE compra_id = %s
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, (compra_id,))
    finally:
        cursor.close()

