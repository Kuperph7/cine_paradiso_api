"""Consultas SQL relacionadas con funciones."""

# Issue #32 - Obtener las funciones de una pelicula
def listar_funciones_de_pelicula(conexion, pelicula_id):
    consulta = """
        SELECT
            f.id,
            f.fecha_hora,
            f.precio,
            s.id AS sala_id,
            s.nombre AS sala_nombre,
            l.id AS local_id,
            l.nombre AS local_nombre
        FROM funciones AS f
        INNER JOIN salas AS s
            ON s.id = f.sala_id
        INNER JOIN locales AS l
            ON l.id = s.local_id
        WHERE f.pelicula_id = %s
          AND f.estado = 'programada'
          AND f.fecha_hora >= NOW()
          AND s.activa = TRUE
          AND l.activa = TRUE
        ORDER BY f.fecha_hora, f.id
    """

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, (pelicula_id,))
        return cursor.fetchall()
    finally:
        cursor.close()
