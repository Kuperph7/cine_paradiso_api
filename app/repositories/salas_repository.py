"""Consultas SQL relacionadas con salas y butacas."""


CAMPOS_ACTUALIZABLES = ("nombre", "filas", "butacas_por_fila", "activa")


def listar_salas(conexion, incluir_inactivas=False):
    condicion = "" if incluir_inactivas else "WHERE s.activa = TRUE"
    consulta = f"""
        SELECT
            s.id,
            s.local_id,
            s.nombre,
            s.filas,
            s.butacas_por_fila,
            s.filas * s.butacas_por_fila AS capacidad,
            s.activa
        FROM salas AS s
        {condicion}
        ORDER BY s.local_id, s.nombre, s.id
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta)
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_sala_por_id(conexion, sala_id, bloquear=False):
    bloqueo = " FOR UPDATE" if bloquear else ""
    consulta = f"""
        SELECT
            id,
            local_id,
            nombre,
            filas,
            butacas_por_fila,
            filas * butacas_por_fila AS capacidad,
            activa
        FROM salas
        WHERE id = %s{bloqueo}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (sala_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def buscar_local_por_id(conexion, local_id):
    consulta = """
        SELECT id, activa
        FROM locales
        WHERE id = %s
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (local_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def existe_sala_con_nombre(
    conexion,
    local_id,
    nombre,
    excluir_id=None,
):
    consulta = """
        SELECT id
        FROM salas
        WHERE local_id = %s
          AND nombre = %s
    """
    parametros = [local_id, nombre]
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


def crear_sala(conexion, datos):
    consulta = """
        INSERT INTO salas
            (local_id, nombre, filas, butacas_por_fila, activa)
        VALUES (%s, %s, %s, %s, TRUE)
    """
    parametros = (
        datos["local_id"],
        datos["nombre"],
        datos["filas"],
        datos["butacas_por_fila"],
    )
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, parametros)
        return cursor.lastrowid
    finally:
        cursor.close()


def actualizar_sala(conexion, sala_id, cambios):
    campos = [campo for campo in CAMPOS_ACTUALIZABLES if campo in cambios]
    asignaciones = ", ".join(f"{campo} = %s" for campo in campos)
    parametros = [cambios[campo] for campo in campos]
    parametros.append(sala_id)

    cursor = conexion.cursor()
    try:
        cursor.execute(
            f"UPDATE salas SET {asignaciones} WHERE id = %s",
            tuple(parametros),
        )
    finally:
        cursor.close()


def listar_butacas_de_sala(conexion, sala_id):
    consulta = """
        SELECT id, fila, numero
        FROM butacas
        WHERE sala_id = %s
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (sala_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def crear_butacas(conexion, sala_id, coordenadas):
    parametros = [
        (sala_id, fila, numero)
        for fila, numero in coordenadas
    ]
    if not parametros:
        return

    consulta = """
        INSERT INTO butacas (sala_id, fila, numero, activa)
        VALUES (%s, %s, %s, TRUE)
    """
    cursor = conexion.cursor()
    try:
        cursor.executemany(consulta, parametros)
    finally:
        cursor.close()


def desactivar_butacas_de_sala(conexion, sala_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            "UPDATE butacas SET activa = FALSE WHERE sala_id = %s",
            (sala_id,),
        )
    finally:
        cursor.close()


def activar_butacas(conexion, butaca_ids):
    parametros = [(butaca_id,) for butaca_id in butaca_ids]
    if not parametros:
        return

    cursor = conexion.cursor()
    try:
        cursor.executemany(
            "UPDATE butacas SET activa = TRUE WHERE id = %s",
            parametros,
        )
    finally:
        cursor.close()

