"""Servicios de cartelera, películas y funciones."""

from app.db import get_db_connection
from app.errors import ApiError

from app.repositories.peliculas_repository import (
    listar_peliculas,
    buscar_pelicula
)
from app.repositories.funciones_repository import (
    listar_funciones_de_pelicula
)


# Issue #31 - Consultar peliculas de la cartelera
def consultar_peliculas(local_id=None, fecha=None):
    conexion = get_db_connection()

    try:
        peliculas = listar_peliculas(conexion, local_id, fecha)

        for pelicula in peliculas:
            genero = pelicula.pop("genero", None)
            pelicula["generos"] = [genero] if genero else []

        return {"peliculas": peliculas}

    finally:
        conexion.close()


# Issue #32 - Consultar una pelicula y sus funciones
def consultar_detalle_pelicula(pelicula_id):
    conexion = get_db_connection()

    try:
        pelicula = buscar_pelicula(conexion, pelicula_id)

        if pelicula is None:
            raise ApiError(
                404,
                "PELICULA_NO_ENCONTRADA",
                "Película no encontrada",
                "No existe una película activa con ese identificador."
            )

        funciones = listar_funciones_de_pelicula(
            conexion, pelicula_id
        )

        genero = pelicula.pop("genero", None)
        pelicula["generos"] = [genero] if genero else []

        for funcion in funciones:
            funcion["fecha_hora"] = funcion["fecha_hora"].isoformat()
            funcion["precio"] = float(funcion["precio"])

        pelicula["funciones_disponibles"] = funciones

        return pelicula

    finally:
        conexion.close()
