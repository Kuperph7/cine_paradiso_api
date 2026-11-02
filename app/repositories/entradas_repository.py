"""Consultas SQL relacionadas con entradas."""


def crear_entrada(
    conexion,
    compra_id,
    butaca_funcion_id,
    precio,
    codigo_qr,
):
    consulta = """
        INSERT INTO entradas (
            compra_id,
            butaca_funcion_id,
            precio,
            codigo_qr,
            estado
        )
        VALUES (%s, %s, %s, %s, 'vigente')
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(
            consulta,
            (compra_id, butaca_funcion_id, precio, codigo_qr),
        )
        return cursor.lastrowid
    finally:
        cursor.close()


def listar_entradas_compra(conexion, compra_id):
    consulta = """
        SELECT
            e.id,
            e.compra_id,
            c.usuario_id,
            c.funcion_id,
            b.id AS butaca_id,
            b.fila,
            b.numero,
            bf.estado AS estado_butaca,
            e.codigo_qr,
            e.estado,
            e.fecha_hora_validacion AS utilizada_en
        FROM entradas AS e
        INNER JOIN compras AS c ON c.id = e.compra_id
        INNER JOIN butacas_funcion AS bf ON bf.id = e.butaca_funcion_id
        INNER JOIN butacas AS b ON b.id = bf.butaca_id
        WHERE e.compra_id = %s
        ORDER BY b.fila, b.numero, e.id
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (compra_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def bloquear_entradas_compra(conexion, compra_id):
    consulta = """
        SELECT id, estado
        FROM entradas
        WHERE compra_id = %s
        ORDER BY id
        FOR UPDATE
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, (compra_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def cancelar_entradas_compra(conexion, compra_id):
    consulta = """
        UPDATE entradas
        SET estado = 'cancelada',
            fecha_hora_cancelacion = CURRENT_TIMESTAMP
        WHERE compra_id = %s
    """
    cursor = conexion.cursor()
    try:
        cursor.execute(consulta, (compra_id,))
    finally:
        cursor.close()

