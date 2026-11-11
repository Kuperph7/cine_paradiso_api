"""Consultas SQL relacionadas con estadísticas."""


def _filtro_fechas(alias, filtros):
    condiciones = []
    parametros = []

    if filtros["desde"] is not None:
        condiciones.append(f"{alias}.fecha_hora >= %s")
        parametros.append(filtros["desde"])

        condiciones.append(f"{alias}.fecha_hora <= %s")
        parametros.append(filtros["hasta"])

    return condiciones, parametros


def obtener_ocupacion_por_funcion(conexion, filtros):
    condiciones, parametros = _filtro_fechas("f", filtros)

    where = (
        f"WHERE {' AND '.join(condiciones)}"
        if condiciones else ""
    )

    consulta = f"""
        SELECT
            f.id AS funcion_id,
            COUNT(
                DISTINCT CASE
                    WHEN c.estado = 'confirmada'
                     AND e.estado IN ('vigente', 'utilizada')
                    THEN e.id
                END
            ) AS butacas_vendidas,
            s.filas * s.butacas_por_fila AS capacidad
        FROM funciones AS f
        INNER JOIN salas AS s
            ON s.id = f.sala_id
        LEFT JOIN compras AS c
            ON c.funcion_id = f.id
        LEFT JOIN entradas AS e
            ON e.compra_id = c.id
        {where}
        GROUP BY f.id, s.filas, s.butacas_por_fila
        ORDER BY f.id
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def obtener_ocupacion_por_pelicula(conexion, filtros):
    condiciones, parametros = _filtro_fechas("f", filtros)

    where = (
        f"WHERE {' AND '.join(condiciones)}"
        if condiciones else ""
    )

    consulta = f"""
        SELECT
            p.id AS pelicula_id,
            COALESCE(SUM(datos.butacas_vendidas), 0)
                AS butacas_vendidas,
            COALESCE(SUM(datos.capacidad), 0)
                AS capacidad_total_funciones
        FROM peliculas AS p
        INNER JOIN (
            SELECT
                f.id AS funcion_id,
                f.pelicula_id,
                s.filas * s.butacas_por_fila AS capacidad,
                COUNT(
                    DISTINCT CASE
                        WHEN c.estado = 'confirmada'
                         AND e.estado IN ('vigente', 'utilizada')
                        THEN e.id
                    END
                ) AS butacas_vendidas
            FROM funciones AS f
            INNER JOIN salas AS s
                ON s.id = f.sala_id
            LEFT JOIN compras AS c
                ON c.funcion_id = f.id
            LEFT JOIN entradas AS e
                ON e.compra_id = c.id
            {where}
            GROUP BY
                f.id,
                f.pelicula_id,
                s.filas,
                s.butacas_por_fila
        ) AS datos
            ON datos.pelicula_id = p.id
        GROUP BY p.id
        ORDER BY p.id
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def obtener_ventas_por_genero(conexion, filtros):
    condiciones, parametros = _filtro_fechas("f", filtros)

    condiciones.append("c.estado = 'confirmada'")

    where = f"WHERE {' AND '.join(condiciones)}"

    consulta = f"""
        SELECT
            p.genero AS genero,
            COALESCE(SUM(c.total_entradas), 0) AS total_ventas
        FROM compras AS c
        INNER JOIN funciones AS f
            ON f.id = c.funcion_id
        INNER JOIN peliculas AS p
            ON p.id = f.pelicula_id
        {where}
        GROUP BY p.genero
        ORDER BY total_ventas DESC
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def obtener_ventas_por_franja(conexion, filtros):
    condiciones, parametros = _filtro_fechas("f", filtros)

    condiciones.append("c.estado = 'confirmada'")
    condiciones.append(
        "e.estado IN ('vigente', 'utilizada')"
    )

    where = f"WHERE {' AND '.join(condiciones)}"

    consulta = f"""
        SELECT
            FLOOR(HOUR(f.fecha_hora) / 3) * 3 AS hora_inicio,
            COUNT(DISTINCT e.id) AS entradas_vendidas
        FROM funciones AS f
        INNER JOIN compras AS c
            ON c.funcion_id = f.id
        INNER JOIN entradas AS e
            ON e.compra_id = c.id
        {where}
        GROUP BY hora_inicio
        ORDER BY entradas_vendidas DESC
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchall()
    finally:
        cursor.close()


def obtener_total_cancelaciones(conexion, filtros):
    condiciones, parametros = _filtro_fechas("c", filtros)

    condiciones.append("c.estado = 'cancelada'")

    where = f"WHERE {' AND '.join(condiciones)}"

    consulta = f"""
        SELECT
            COUNT(*) AS cancelaciones
        FROM compras AS c
        {where}
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchone()
    finally:
        cursor.close()
