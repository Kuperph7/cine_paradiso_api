"""Consultas SQL relacionadas con compras y servicios."""


def bloquear_butacas(conexion, sala_id, butaca_ids):
    marcadores = ", ".join(["%s"] * len(butaca_ids))
    consulta = f"""
        SELECT id
        FROM butacas
        WHERE sala_id = %s
          AND activa = TRUE
          AND id IN ({marcadores})
        ORDER BY id
        FOR UPDATE
    """
    parametros = (sala_id, *sorted(butaca_ids))
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, parametros)
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_ocupaciones_butacas(conexion, funcion_id, butaca_ids):
    marcadores = ", ".join(["%s"] * len(butaca_ids))
    consulta = f"""
        SELECT
            id,
            butaca_id,
            estado,
            reserva_hasta,
            reserva_id,
            CASE
                WHEN reserva_hasta IS NOT NULL
                     AND reserva_hasta > UTC_TIMESTAMP()
                THEN TRUE
                ELSE FALSE
            END AS vigente
        FROM butacas_funcion
        WHERE funcion_id = %s
          AND butaca_id IN ({marcadores})
        ORDER BY butaca_id
        FOR UPDATE
    """
    parametros = (funcion_id, *sorted(butaca_ids))
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, parametros)
        return cursor.fetchall()
    finally:
        cursor.close()


def ocupar_butacas(conexion, funcion_id, butaca_ids):
    consulta = """
        INSERT INTO butacas_funcion
            (funcion_id, butaca_id, estado, reserva_hasta)
        VALUES (%s, %s, 'ocupada', NULL)
        ON DUPLICATE KEY UPDATE
            estado = 'ocupada',
            reserva_hasta = NULL
    """
    parametros = [(funcion_id, butaca_id) for butaca_id in sorted(butaca_ids)]
    cursor = conexion.cursor()
    try:
        cursor.executemany(consulta, parametros)
    finally:
        cursor.close()


def buscar_butacas_funcion(conexion, funcion_id, butaca_ids):
    marcadores = ", ".join(["%s"] * len(butaca_ids))
    consulta = f"""
        SELECT id, butaca_id
        FROM butacas_funcion
        WHERE funcion_id = %s
          AND butaca_id IN ({marcadores})
    """
    parametros = (funcion_id, *sorted(butaca_ids))
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, parametros)
        return cursor.fetchall()
    finally:
        cursor.close()


def crear_compra(
    conexion,
    usuario_id,
    funcion_id,
    reserva_id,
    medio_pago,
    total_entradas,
    total_servicios,
    total,
    estado="pendiente_pago",
):
    consulta = """
        INSERT INTO compras (
            usuario_id,
            funcion_id,
            reserva_id,
            estado,
            medio_pago,
            fecha_hora,
            total_entradas,
            total_servicios,
            total
        )
        VALUES (%s, %s, %s, %s, %s, UTC_TIMESTAMP(), %s, %s, %s)
    """
    parametros = (
        usuario_id,
        funcion_id,
        reserva_id,
        estado,
        medio_pago,
        total_entradas,
        total_servicios,
        total,
    )
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, parametros)
        return cursor.lastrowid
    finally:
        cursor.close()


def agregar_servicios_compra(conexion, compra_id, servicios):
    if not servicios:
        return

    consulta = """
        INSERT INTO compras_servicios
            (compra_id, servicio_id, cantidad, precio_unitario, subtotal)
        VALUES (%s, %s, %s, %s, %s)
    """
    parametros = [
        (
            compra_id,
            servicio["servicio_id"],
            servicio["cantidad"],
            servicio["precio_unitario"],
            servicio["subtotal"],
        )
        for servicio in servicios
    ]
    cursor = conexion.cursor()
    try:
        cursor.executemany(consulta, parametros)
    finally:
        cursor.close()


def contar_estacionamientos_ocupados(
    conexion,
    servicio_id,
    duracion_segundos,
    funcion_id=None,
    excluir_compra_id=None,
):
    """Cuenta lugares ocupados dentro de la ventana temporal de la función."""
    exclusion = ""
    join_funcion = ""
    condicion_funcion = ""
    parametros = []

    if funcion_id is not None:
        join_funcion = (
            "INNER JOIN funciones AS f ON f.id = c.funcion_id "
            "INNER JOIN funciones AS f_actual ON f_actual.id = %s"
        )
        condicion_funcion = (
            "AND ABS(TIMESTAMPDIFF(SECOND, f.fecha_hora, f_actual.fecha_hora)) < %s"
        )
        parametros.append(funcion_id)

    parametros.append(servicio_id)
    if funcion_id is not None:
        parametros.append(duracion_segundos)
    parametros.append(duracion_segundos)

    if excluir_compra_id is not None:
        exclusion = "AND c.id <> %s"
        parametros.append(excluir_compra_id)

    consulta = f"""
        SELECT COALESCE(SUM(cs.cantidad), 0) AS cantidad
        FROM compras_servicios AS cs
        INNER JOIN compras AS c ON c.id = cs.compra_id
        {join_funcion}
        LEFT JOIN reservas AS r ON r.id = c.reserva_id
        WHERE cs.servicio_id = %s
          {condicion_funcion}
          AND (
              (
                  c.estado = 'confirmada'
                  AND c.fecha_hora > DATE_SUB(UTC_TIMESTAMP(), INTERVAL %s SECOND)
              )
              OR (
                  c.estado = 'pendiente_pago'
                  AND r.estado = 'pago_en_proceso'
                  AND r.expira_en > UTC_TIMESTAMP()
              )
          )
          {exclusion}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return int(cursor.fetchone()["cantidad"])
    finally:
        cursor.close()

def listar_compras(conexion, usuario_id=None, estado=None):
    condiciones = []
    parametros = []
    if usuario_id is not None:
        condiciones.append("c.usuario_id = %s")
        parametros.append(usuario_id)
    if estado is not None:
        condiciones.append("c.estado = %s")
        parametros.append(estado)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    consulta = f"""
        SELECT
            c.id,
            c.usuario_id,
            c.funcion_id,
            c.reserva_id,
            c.estado,
            c.medio_pago,
            c.fecha_hora,
            c.total_entradas,
            c.total_servicios,
            c.total,
            f.fecha_hora AS funcion_fecha_hora
        FROM compras AS c
        INNER JOIN funciones AS f ON f.id = c.funcion_id
        {where}
        ORDER BY c.fecha_hora DESC, c.id DESC
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_compra_por_id(conexion, compra_id, bloquear=False):
    bloqueo = " FOR UPDATE" if bloquear else ""
    consulta = f"""
        SELECT
            c.id,
            c.usuario_id,
            c.funcion_id,
            c.reserva_id,
            c.estado,
            c.medio_pago,
            c.fecha_hora,
            c.total_entradas,
            c.total_servicios,
            c.total,
            f.fecha_hora AS funcion_fecha_hora
        FROM compras AS c
        INNER JOIN funciones AS f ON f.id = c.funcion_id
        WHERE c.id = %s{bloqueo}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (compra_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def listar_servicios_compra(conexion, compra_id):
    consulta = """
        SELECT
            cs.servicio_id,
            s.nombre,
            cs.cantidad,
            cs.precio_unitario,
            cs.subtotal
        FROM compras_servicios AS cs
        INNER JOIN servicios AS s ON s.id = cs.servicio_id
        WHERE cs.compra_id = %s
        ORDER BY cs.id
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (compra_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def confirmar_compra(conexion, compra_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE compras
            SET estado = 'confirmada',
                fecha_hora = UTC_TIMESTAMP()
            WHERE id = %s
              AND estado = 'pendiente_pago'
            """,
            (compra_id,),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def cancelar_compra(conexion, compra_id, motivo):
    consulta = """
        UPDATE compras
        SET estado = 'cancelada',
            motivo_cancelacion = %s
        WHERE id = %s
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, (motivo, compra_id))
    finally:
        cursor.close()


def liberar_butacas_compra(conexion, compra_id):
    consulta = """
        UPDATE butacas_funcion AS bf
        INNER JOIN entradas AS e ON e.butaca_funcion_id = bf.id
        SET bf.estado = 'disponible',
            bf.reserva_hasta = NULL,
            bf.reserva_id = NULL
        WHERE e.compra_id = %s
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, (compra_id,))
    finally:
        cursor.close()

