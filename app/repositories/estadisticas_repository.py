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
            f.fecha_hora,
            p.id AS pelicula_id,
            p.titulo AS pelicula_titulo,
            s.nombre AS sala_nombre,
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
        INNER JOIN peliculas AS p
            ON p.id = f.pelicula_id
        LEFT JOIN compras AS c
            ON c.funcion_id = f.id
        LEFT JOIN entradas AS e
            ON e.compra_id = c.id
        {where}
        GROUP BY
            f.id, f.fecha_hora, p.id, p.titulo,
            s.nombre, s.filas, s.butacas_por_fila
        ORDER BY f.fecha_hora DESC, f.id DESC
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
            p.titulo,
            p.genero,
            COUNT(datos.funcion_id) AS cantidad_funciones,
            COALESCE(SUM(datos.butacas_vendidas), 0) AS butacas_vendidas,
            COALESCE(SUM(datos.capacidad), 0) AS capacidad_total_funciones
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
        GROUP BY p.id, p.titulo, p.genero
        ORDER BY p.titulo
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
            COALESCE(NULLIF(TRIM(p.genero), ''), 'Sin género') AS genero,
            COUNT(DISTINCT e.id) AS total_ventas
        FROM compras AS c
        INNER JOIN entradas AS e
            ON e.compra_id = c.id
        INNER JOIN funciones AS f
            ON f.id = c.funcion_id
        INNER JOIN peliculas AS p
            ON p.id = f.pelicula_id
        {where}
        GROUP BY genero
        ORDER BY total_ventas DESC, genero
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
            c.id AS compra_id,
            f.id AS funcion_id,
            f.fecha_hora AS funcion_fecha_hora,
            p.titulo AS pelicula_titulo,
            COALESCE(MAX(e.fecha_hora_cancelacion), c.fecha_hora)
                AS fecha_cancelacion,
            c.motivo_cancelacion,
            COUNT(e.id) AS cantidad_entradas
        FROM compras AS c
        INNER JOIN funciones AS f
            ON f.id = c.funcion_id
        INNER JOIN peliculas AS p
            ON p.id = f.pelicula_id
        LEFT JOIN entradas AS e
            ON e.compra_id = c.id
        {where}
        GROUP BY
            c.id, f.id, f.fecha_hora, p.titulo,
            c.fecha_hora, c.motivo_cancelacion
        ORDER BY fecha_cancelacion DESC, c.id DESC
    """

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchone()
    finally:
        cursor.close()

def obtener_funciones_canceladas(conexion, filtros):
    condiciones, parametros = _filtro_fechas("f", filtros)
    condiciones.append("f.estado = 'cancelada'")

    where = f"WHERE {' AND '.join(condiciones)}"

    consulta = f"""
        SELECT
            f.id AS funcion_id,
            f.fecha_hora,
            p.titulo AS pelicula_titulo,
            s.nombre AS sala_nombre,
            COUNT(DISTINCT c.id) AS compras_afectadas
        FROM funciones AS f
        INNER JOIN peliculas AS p
            ON p.id = f.pelicula_id
        INNER JOIN salas AS s
            ON s.id = f.sala_id
        LEFT JOIN compras AS c
            ON c.funcion_id = f.id
        {where}
        GROUP BY f.id, f.fecha_hora, p.titulo, s.nombre
        ORDER BY f.fecha_hora DESC, f.id DESC
    """
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(consulta, tuple(parametros))
        return cursor.fetchone()
    finally:
        cursor.close()
