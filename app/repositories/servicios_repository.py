"""Consultas SQL relacionadas con servicios adicionales."""
from app.db import get_db_connection


def obtener_todos_los_servicios(incluir_inactivos=True):
    """Obtiene servicios ordenados y permite excluir los inactivos."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT id, nombre, descripcion, precio, activo
            FROM servicios
        """
        if not incluir_inactivos:
            query += " WHERE activo = TRUE"
        query += " ORDER BY id"
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def obtener_servicio_por_id(servicio_id: int):
    """Busca un servicio por su identificador único."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, nombre, descripcion, precio, activo FROM servicios WHERE id = %s"
        cursor.execute(query, (servicio_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def obtener_servicio_por_nombre(nombre: str):
    """Busca un servicio por su nombre exacto."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = "SELECT id, nombre, descripcion, precio, activo FROM servicios WHERE nombre = %s"
        cursor.execute(query, (nombre,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def crear_servicio(nombre: str, descripcion: str, precio: int, activo: bool = True) -> int:
    """Inserta un nuevo servicio adicional y retorna su id generado."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT INTO servicios (nombre, descripcion, precio, activo)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (nombre, descripcion, precio, activo))
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def actualizar_servicio(servicio_id: int, campos: dict):
    """Actualiza dinámicamente los campos especificados de un servicio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        set_clauses = []
        valores = []
        for campo, valor in campos.items():
            set_clauses.append(f"{campo} = %s")
            valores.append(valor)
        valores.append(servicio_id)
        query = f"UPDATE servicios SET {', '.join(set_clauses)} WHERE id = %s"
        cursor.execute(query, tuple(valores))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def dar_de_baja_servicio(servicio_id: int):
    """Realiza una baja lógica desactivando el servicio sin eliminarlo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "UPDATE servicios SET activo = FALSE WHERE id = %s"
        cursor.execute(query, (servicio_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def buscar_servicios_por_ids(conexion, servicio_ids):
    if not servicio_ids:
        return []

    marcadores = ", ".join(["%s"] * len(servicio_ids))
    consulta = f"""
        SELECT id, nombre, precio, activo
        FROM servicios
        WHERE id IN ({marcadores})
        ORDER BY id
        FOR UPDATE
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(sorted(servicio_ids)))
        return cursor.fetchall()
    finally:
        cursor.close()

def eliminar_servicio(servicio_id):
    """Compatibilidad: eliminar un servicio realiza una baja lógica."""
    dar_de_baja_servicio(servicio_id)
