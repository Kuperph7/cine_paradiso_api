"""Consultas SQL relacionadas con salas y butacas."""


def buscar_sala_por_id(conexion, sala_id):
    consulta = """
        SELECT id, activa
        FROM salas
        WHERE id = %s
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (sala_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

