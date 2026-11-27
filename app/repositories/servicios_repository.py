"""Consultas SQL relacionadas con servicios adicionales."""
from app.db import get_db_connection


def asegurar_servicio_estacionamiento(servicio_id):
    """Garantiza que exista el servicio de estacionamiento en la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = """
            INSERT IGNORE INTO servicios (id, nombre, descripcion, precio, activo)
            VALUES (%s, 'Estacionamiento', 'Lugar de estacionamiento por 3 horas.', 5000, TRUE)
        """
        cursor.execute(query, (servicio_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def obtener_estacionamientos_ocupados(
    servicio_id,
    duracion_segundos,
    funcion_id=None,
):
    """Devuelve cuántos lugares de estacionamiento están ocupados actualmente."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if funcion_id is not None:
            query = """
                SELECT COALESCE(SUM(cs.cantidad), 0) AS cantidad
                FROM compras_servicios AS cs
                INNER JOIN compras AS c ON c.id = cs.compra_id
                INNER JOIN funciones AS f ON f.id = c.funcion_id
                INNER JOIN funciones AS f_actual ON f_actual.id = %s
                LEFT JOIN reservas AS r ON r.id = c.reserva_id
                WHERE cs.servicio_id = %s
                  AND ABS(TIMESTAMPDIFF(SECOND, f.fecha_hora, f_actual.fecha_hora)) < %s
                  AND (
                      (
                          c.estado = 'confirmada'
                          AND c.fecha_hora > DATE_SUB(UTC_TIMESTAMP(), INTERVAL %s SECOND)
                      )
                      OR (
                          c.estado = 'pendiente_pago'
                          AND r.estado = 'pago_en_proceso'
                          AND r.expira_en > UTC_TIMESTAMP()
                      )
                  )
            """
            parametros = (
                funcion_id,
                servicio_id,
                duracion_segundos,
                duracion_segundos,
            )
        else:
            query = """
                SELECT COALESCE(SUM(cs.cantidad), 0) AS cantidad
                FROM compras_servicios AS cs
                INNER JOIN compras AS c ON c.id = cs.compra_id
                LEFT JOIN reservas AS r ON r.id = c.reserva_id
                WHERE cs.servicio_id = %s
                  AND (
                      (
                          c.estado = 'confirmada'
                          AND c.fecha_hora > DATE_SUB(UTC_TIMESTAMP(), INTERVAL %s SECOND)
                      )
                      OR (
                          c.estado = 'pendiente_pago'
                          AND r.estado = 'pago_en_proceso'
                          AND r.expira_en > UTC_TIMESTAMP()
                      )
                  )
            """
            parametros = (servicio_id, duracion_segundos)
        cursor.execute(query, parametros)
        return int(cursor.fetchone()["cantidad"])
    finally:
        cursor.close()
        conn.close()


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


def obtener_servicio_por_id(servicio_id):
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


def obtener_servicio_por_nombre(nombre):
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


def crear_servicio(nombre, descripcion, precio, activo=True):
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


def actualizar_servicio(servicio_id, campos):
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


def dar_de_baja_servicio(servicio_id):
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
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM servicios WHERE id = %s",
            (servicio_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()
