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


def existe_funcion_en_horario(conexion, sala_id, fecha_hora, excluir_id=None):
    consulta = """
        SELECT id
        FROM funciones
        WHERE sala_id = %s
          AND fecha_hora = %s
    """
    parametros = [sala_id, fecha_hora]
    if excluir_id is not None:
        consulta += " AND id <> %s"
        parametros.append(excluir_id)
    consulta += " LIMIT 1"

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchone() is not None
    finally:
        cursor.close()


def crear_funcion(conexion, datos):
    consulta = """
        INSERT INTO funciones
            (pelicula_id, sala_id, fecha_hora, precio, estado)
        VALUES (%s, %s, %s, %s, %s)
    """
    parametros = (
        datos["pelicula_id"],
        datos["sala_id"],
        datos["fecha_hora"],
        datos["precio"],
        datos["estado"],
    )
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, parametros)
        return cursor.lastrowid
    finally:
        cursor.close()


def actualizar_funcion(conexion, funcion_id, cambios):
    campos = [campo for campo in CAMPOS_ACTUALIZABLES if campo in cambios]
    asignaciones = ", ".join(f"{campo} = %s" for campo in campos)
    parametros = [cambios[campo] for campo in campos]
    parametros.append(funcion_id)

    cursor = conexion.cursor()
    try:
        cursor.execute(
            f"UPDATE funciones SET {asignaciones} WHERE id = %s",
            tuple(parametros),
        )
    finally:
        cursor.close()


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

