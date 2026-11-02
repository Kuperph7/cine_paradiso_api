"""Consultas SQL relacionadas con servicios adicionales."""


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

