"""Consultas SQL relacionadas con películas."""


def buscar_pelicula_por_id(conexion, pelicula_id):
    consulta = """
        SELECT id, activa
        FROM peliculas
        WHERE id = %s
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (pelicula_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

