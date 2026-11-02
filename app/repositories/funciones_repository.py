"""Consultas SQL relacionadas con funciones."""


CAMPOS_ACTUALIZABLES = (
    "pelicula_id",
    "sala_id",
    "fecha_hora",
    "precio",
    "estado",
)


def listar_funciones(
    conexion,
    pelicula_id=None,
    desde=None,
    hasta=None,
    estado=None,
    solo_publicadas=True,
):
    condiciones = []
    parametros = []

    if solo_publicadas:
        condiciones.extend(
            [
                "f.estado = 'programada'",
                "f.fecha_hora >= NOW()",
                "p.activa = TRUE",
                "s.activa = TRUE",
            ]
        )
    if pelicula_id is not None:
        condiciones.append("f.pelicula_id = %s")
        parametros.append(pelicula_id)
    if desde is not None:
        condiciones.append("f.fecha_hora >= %s")
        parametros.append(desde)
    if hasta is not None:
        condiciones.append("f.fecha_hora <= %s")
        parametros.append(hasta)
    if estado is not None:
        condiciones.append("f.estado = %s")
        parametros.append(estado)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    consulta = f"""
        SELECT
            f.id,
            f.pelicula_id,
            f.sala_id,
            f.fecha_hora,
            f.precio,
            f.estado
        FROM funciones AS f
        INNER JOIN peliculas AS p ON p.id = f.pelicula_id
        INNER JOIN salas AS s ON s.id = f.sala_id
        {where}
        ORDER BY f.fecha_hora, f.id
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_funcion_por_id(conexion, funcion_id, bloquear=False):
    bloqueo = " FOR UPDATE" if bloquear else ""
    consulta = f"""
        SELECT id, pelicula_id, sala_id, fecha_hora, precio, estado
        FROM funciones
        WHERE id = %s{bloqueo}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (funcion_id,))
        return cursor.fetchone()
    finally:
        cursor.close()

