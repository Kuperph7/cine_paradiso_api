"""Consultas SQL del ciclo de vida de reservas temporales."""


def crear_reserva(conexion, reserva_id, usuario_id, funcion_id):
    consulta = """
        INSERT INTO reservas (
            id,
            usuario_id,
            funcion_id,
            estado,
            creada_en,
            expira_en,
            actualizada_en
        )
        VALUES (
            %s,
            %s,
            %s,
            'retenida',
            UTC_TIMESTAMP(),
            UTC_TIMESTAMP() + INTERVAL 5 MINUTE,
            UTC_TIMESTAMP()
        )
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, (reserva_id, usuario_id, funcion_id))
    finally:
        cursor.close()

def buscar_reserva(conexion, reserva_id, bloquear=False):
    bloqueo = " FOR UPDATE" if bloquear else ""
    consulta = f"""
        SELECT
            r.id,
            r.usuario_id,
            r.funcion_id,
            r.estado,
            r.creada_en,
            r.expira_en,
            r.idempotencia_pago,
            r.compra_id,
            r.actualizada_en,
            r.expira_en > UTC_TIMESTAMP() AS vigente
        FROM reservas AS r
        WHERE r.id = %s{bloqueo}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (reserva_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def buscar_reserva_activa_usuario(conexion, usuario_id):
    consulta = """
        SELECT
            r.id,
            r.usuario_id,
            r.funcion_id,
            r.estado,
            r.creada_en,
            r.expira_en,
            r.idempotencia_pago,
            r.compra_id,
            r.actualizada_en,
            r.expira_en > UTC_TIMESTAMP() AS vigente
        FROM reservas AS r
        WHERE r.usuario_id = %s
          AND r.estado IN ('retenida', 'pago_en_proceso')
          AND r.expira_en > UTC_TIMESTAMP()
        ORDER BY
            CASE WHEN r.estado = 'pago_en_proceso' THEN 0 ELSE 1 END,
            r.actualizada_en DESC
        LIMIT 1
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (usuario_id,))
        return cursor.fetchone()
    finally:
        cursor.close()


def listar_butacas_reserva(conexion, reserva_id, bloquear=False):
    bloqueo = " FOR UPDATE" if bloquear else ""
    consulta = f"""
        SELECT
            bf.id AS butaca_funcion_id,
            bf.butaca_id,
            bf.estado,
            bf.reserva_hasta,
            bf.reserva_id,
            b.fila,
            b.numero
        FROM butacas_funcion AS bf
        INNER JOIN butacas AS b ON b.id = bf.butaca_id
        WHERE bf.reserva_id = %s
        ORDER BY bf.butaca_id{bloqueo}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (reserva_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def buscar_reservas_por_ids(conexion, reserva_ids, bloquear=False):
    if not reserva_ids:
        return []
    marcadores = ", ".join(["%s"] * len(reserva_ids))
    bloqueo = " FOR UPDATE" if bloquear else ""
    consulta = f"""
        SELECT
            id,
            usuario_id,
            funcion_id,
            estado,
            expira_en,
            compra_id,
            expira_en > UTC_TIMESTAMP() AS vigente
        FROM reservas
        WHERE id IN ({marcadores})
        ORDER BY id{bloqueo}
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(sorted(reserva_ids)))
        return cursor.fetchall()
    finally:
        cursor.close()


def retener_butacas(conexion, reserva_id, funcion_id, butaca_ids):
    consulta = """
        INSERT INTO butacas_funcion (
            funcion_id,
            butaca_id,
            estado,
            reserva_hasta,
            reserva_id
        )
        SELECT %s, %s, 'retenida', r.expira_en, r.id
        FROM reservas AS r
        WHERE r.id = %s
        ON DUPLICATE KEY UPDATE
            estado = VALUES(estado),
            reserva_hasta = VALUES(reserva_hasta),
            reserva_id = VALUES(reserva_id)
    """
    parametros = [
        (funcion_id, butaca_id, reserva_id)
        for butaca_id in sorted(butaca_ids)
    ]
    cursor = conexion.cursor()
    try:
        # mysql-connector no puede reescribir INSERT ... SELECT como batch.
        # La transaccion ya protege la seleccion completa; se ejecutan en orden
        # estable para conservar atomicidad y evitar interbloqueos.
        for parametro in parametros:
            cursor.execute(consulta, parametro)
    finally:
        cursor.close()


def cancelar_reserva(conexion, reserva_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE reservas
            SET estado = 'cancelada',
                actualizada_en = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (reserva_id,),
        )
    finally:
        cursor.close()


def liberar_butacas_reserva(conexion, reserva_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE butacas_funcion
            SET estado = 'disponible',
                reserva_hasta = NULL,
                reserva_id = NULL
            WHERE reserva_id = %s
              AND estado IN ('retenida', 'pago_en_proceso')
            """,
            (reserva_id,),
        )
    finally:
        cursor.close()


def marcar_reservas_vencidas(conexion, reserva_ids):
    if not reserva_ids:
        return
    marcadores = ", ".join(["%s"] * len(reserva_ids))
    cursor = conexion.cursor()
    try:
        cursor.execute(
            f"""
            UPDATE reservas
            SET estado = 'vencida',
                actualizada_en = UTC_TIMESTAMP()
            WHERE id IN ({marcadores})
              AND estado IN ('retenida', 'pago_en_proceso')
              AND expira_en <= UTC_TIMESTAMP()
            """,
            tuple(sorted(reserva_ids)),
        )
        cursor.execute(
            f"""
            UPDATE compras
            SET estado = 'fallida'
            WHERE reserva_id IN ({marcadores})
              AND estado = 'pendiente_pago'
            """,
            tuple(sorted(reserva_ids)),
        )
    finally:
        cursor.close()


def iniciar_pago_reserva(
    conexion,
    reserva_id,
    idempotencia_pago,
    compra_id,
):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE reservas
            SET estado = 'pago_en_proceso',
                expira_en = UTC_TIMESTAMP() + INTERVAL 5 MINUTE,
                idempotencia_pago = %s,
                compra_id = %s,
                actualizada_en = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (idempotencia_pago, compra_id, reserva_id),
        )
        cursor.execute(
            """
            UPDATE butacas_funcion AS bf
            INNER JOIN reservas AS r ON r.id = bf.reserva_id
            SET bf.estado = 'pago_en_proceso',
                bf.reserva_hasta = r.expira_en
            WHERE bf.reserva_id = %s
              AND bf.estado = 'retenida'
            """,
            (reserva_id,),
        )
    finally:
        cursor.close()


def vender_butacas_reserva(conexion, reserva_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE butacas_funcion
            SET estado = 'vendida',
                reserva_hasta = NULL
            WHERE reserva_id = %s
              AND estado = 'pago_en_proceso'
            """,
            (reserva_id,),
        )
        return cursor.rowcount
    finally:
        cursor.close()


def confirmar_reserva(conexion, reserva_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE reservas
            SET estado = 'vendida',
                actualizada_en = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (reserva_id,),
        )
    finally:
        cursor.close()


def rechazar_pago_reserva(conexion, reserva_id):
    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            UPDATE reservas
            SET estado = 'pago_rechazado',
                actualizada_en = UTC_TIMESTAMP()
            WHERE id = %s
            """,
            (reserva_id,),
        )
        cursor.execute(
            """
            UPDATE compras
            SET estado = 'fallida'
            WHERE reserva_id = %s
              AND estado = 'pendiente_pago'
            """,
            (reserva_id,),
        )
    finally:
        cursor.close()


