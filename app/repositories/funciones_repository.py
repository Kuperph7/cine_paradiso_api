"""Consultas SQL relacionadas con funciones."""


def buscar_funcion_para_compra(conexion, funcion_id):
    consulta = """
        SELECT
            f.id,
            f.sala_id,
            f.fecha_hora,
            f.precio,
            f.estado,
            s.activa AS sala_activa,
            p.activa AS pelicula_activa
        FROM funciones AS f
        INNER JOIN salas AS s ON s.id = f.sala_id
        INNER JOIN peliculas AS p ON p.id = f.pelicula_id
        WHERE f.id = %s
        FOR UPDATE
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (funcion_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

