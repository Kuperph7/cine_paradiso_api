"""Consultas SQL relacionadas con películas."""


def listar_peliculas(conexion, local_id=None, fecha=None):
    consulta = """
        SELECT DISTINCT
            p.id,
            p.titulo,
            p.sinopsis,
            p.poster_url,
            p.duracion_minutos,
            p.clasificacion,
            p.genero
        FROM peliculas AS p
        INNER JOIN funciones AS f
            ON f.pelicula_id = p.id
        INNER JOIN salas AS s
            ON s.id = f.sala_id
        INNER JOIN locales AS l
            ON l.id = s.local_id
        WHERE p.activa = TRUE
          AND s.activa = TRUE
          AND l.activa = TRUE
          AND f.estado = 'programada'
          AND f.fecha_hora >= NOW()
    """

    parametros = []

    if local_id is not None:
        consulta += " AND l.id = %s"
        parametros.append(local_id)

    if fecha is not None:
        consulta += " AND DATE(f.fecha_hora) = %s"
        parametros.append(fecha)

    consulta += " ORDER BY p.titulo"

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()




"""Consultas SQL relacionadas con películas."""


# Issue #31 - Listar peliculas de la cartelera
def listar_peliculas(conexion, local_id=None, fecha=None):
    consulta = """
        SELECT DISTINCT
            p.id,
            p.titulo,
            p.sinopsis,
            p.poster_url,
            p.duracion_minutos,
            p.clasificacion,
            p.genero
        FROM peliculas AS p
        INNER JOIN funciones AS f
            ON f.pelicula_id = p.id
        INNER JOIN salas AS s
            ON s.id = f.sala_id
        INNER JOIN locales AS l
            ON l.id = s.local_id
        WHERE p.activa = TRUE
          AND s.activa = TRUE
          AND l.activa = TRUE
          AND f.estado = 'programada'
          AND f.fecha_hora >= NOW()
    """

    parametros = []

    if local_id is not None:
        consulta += " AND l.id = %s"
        parametros.append(local_id)

    if fecha is not None:
        consulta += " AND DATE(f.fecha_hora) = %s"
        parametros.append(fecha)

    consulta += " ORDER BY p.titulo"

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


# Issue #32 - Buscar una pelicula por su ID
def buscar_pelicula(conexion, pelicula_id):
    consulta = """
        SELECT
            id,
            titulo,
            sinopsis,
            poster_url,
            duracion_minutos,
            clasificacion,
            genero
        FROM peliculas
        WHERE id = %s
          AND activa = TRUE
    """

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, (pelicula_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

