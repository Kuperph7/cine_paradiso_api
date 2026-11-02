"""Consultas SQL relacionadas con salas y butacas."""


# Issue #33 - Consultar butacas de una funcion
def listar_butacas_de_funcion(conexion, funcion_id, sala_id):
    consulta = """
        SELECT
            b.id,
            b.fila,
            b.numero AS columna,
            CASE
                WHEN b.activa = FALSE THEN 'inactiva'
                WHEN bf.estado = 'ocupada' THEN 'ocupada'
                WHEN bf.estado = 'reservada' THEN 'reservada'
                ELSE 'disponible'
            END AS estado
        FROM butacas AS b
        LEFT JOIN butacas_funcion AS bf
            ON bf.butaca_id = b.id
            AND bf.funcion_id = %s
        WHERE b.sala_id = %s
        ORDER BY b.fila, b.numero
    """

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, (funcion_id, sala_id))
        return cursor.fetchall()
    finally:
        cursor.close()
