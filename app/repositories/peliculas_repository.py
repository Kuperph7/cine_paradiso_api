"""Consultas SQL relacionadas con películas."""


CAMPOS_ACTUALIZABLES = (
    "titulo",
    "sinopsis",
    "poster_url",
    "duracion_minutos",
    "clasificacion",
    "genero",
    "activa",
)


def listar_peliculas(
    conexion,
    titulo=None,
    incluir_inactivas=False,
    solo_publicadas=True,
):
    condiciones = []
    parametros = []

    if not incluir_inactivas:
        condiciones.append("p.activa = TRUE")
    if solo_publicadas:
        condiciones.append(
            """
            EXISTS (
                SELECT 1
                FROM funciones AS f
                INNER JOIN salas AS s ON s.id = f.sala_id
                WHERE f.pelicula_id = p.id
                  AND f.estado = 'programada'
                  AND f.fecha_hora >= NOW()
                  AND s.activa = TRUE
            )
            """
        )
    if titulo is not None:
        condiciones.append("p.titulo LIKE %s")
        parametros.append(f"%{titulo}%")

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    consulta = f"""
        SELECT
            p.id,
            p.id_externo,
            p.titulo,
            p.sinopsis,
            p.poster_url,
            p.duracion_minutos,
            p.clasificacion,
            p.genero,
            p.activa
        FROM peliculas AS p
        {where}
        ORDER BY p.titulo, p.id
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_pelicula_por_id(conexion, pelicula_id):
    consulta = """
        SELECT
            id,
            id_externo,
            titulo,
            sinopsis,
            poster_url,
            duracion_minutos,
            clasificacion,
            genero,
            activa
        FROM peliculas
        WHERE id = %s
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (pelicula_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def buscar_pelicula_por_id_externo(conexion, id_externo):
    consulta = """
        SELECT id
        FROM peliculas
        WHERE id_externo = %s
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (id_externo,))
        return cursor.fetchone()
    finally:
        cursor.close()


def crear_pelicula(conexion, datos):
    consulta = """
        INSERT INTO peliculas (
            id_externo,
            titulo,
            sinopsis,
            poster_url,
            duracion_minutos,
            clasificacion,
            genero,
            activa
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
    """
    parametros = (
        datos.get("id_externo"),
        datos["titulo"],
        datos["sinopsis"],
        datos["poster_url"],
        datos["duracion_minutos"],
        datos["clasificacion"],
        datos["genero"],
    )
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, parametros)
        return cursor.lastrowid
    finally:
        cursor.close()


def actualizar_pelicula(conexion, pelicula_id, cambios):
    campos = [campo for campo in CAMPOS_ACTUALIZABLES if campo in cambios]
    asignaciones = ", ".join(f"{campo} = %s" for campo in campos)
    parametros = [cambios[campo] for campo in campos]
    parametros.append(pelicula_id)

    cursor = conexion.cursor()
    try:
        cursor.execute(
            f"UPDATE peliculas SET {asignaciones} WHERE id = %s",
            tuple(parametros),
        )
    finally:
        cursor.close()
