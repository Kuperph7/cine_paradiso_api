"""Consultas SQL relacionadas con categorías de películas."""


def listar_categorias(conexion):
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, nombre FROM categorias ORDER BY id")
        return cursor.fetchall()
    finally:
        cursor.close()


def existen_categorias(conexion, categoria_ids):
    if not categoria_ids:
        return True

    marcadores = ", ".join(["%s"] * len(categoria_ids))
    consulta = f"SELECT id FROM categorias WHERE id IN ({marcadores})"
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, tuple(categoria_ids))
        encontrados = {categoria["id"] for categoria in cursor.fetchall()}
        return encontrados == set(categoria_ids)
    finally:
        cursor.close()


def listar_categorias_pelicula(conexion, pelicula_id):
    consulta = """
        SELECT c.id, c.nombre
        FROM categorias AS c
        INNER JOIN peliculas_categorias AS pc ON pc.categoria_id = c.id
        WHERE pc.pelicula_id = %s
        ORDER BY c.id
    """
    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute(consulta, (pelicula_id,))
        return cursor.fetchall()
    finally:
        cursor.close()


def reemplazar_categorias_pelicula(conexion, pelicula_id, categoria_ids):
    cursor = conexion.cursor()

    try:
        cursor.execute(
            "DELETE FROM peliculas_categorias WHERE pelicula_id = %s",
            (pelicula_id,),
        )

        if categoria_ids:
            cursor.executemany(
                """
                INSERT INTO peliculas_categorias (pelicula_id, categoria_id)
                VALUES (%s, %s)
                """,
                [(pelicula_id, categoria_id) for categoria_id in categoria_ids],
            )
    finally:
        cursor.close()