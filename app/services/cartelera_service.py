"""Servicios de cartelera, películas y funciones."""

from app.db import get_db_connection
from app.errors import ApiError

from app.repositories.peliculas_repository import (
    listar_peliculas,
    buscar_pelicula
)
from app.repositories.funciones_repository import (
    listar_funciones_de_pelicula,
    buscar_funcion_cartelera
)
from app.repositories.salas_repository import (
    listar_butacas_de_funcion
)


# Issue #31 - Listar peliculas
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


# Issue #32 - Detalle de una pelicula
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


# Issue #33 - Disponibilidad de butacas
def consultar_butacas_funcion(funcion_id):
    conexion = get_db_connection()

    try:
        funcion = buscar_funcion_cartelera(conexion, funcion_id)

        if funcion is None:
            raise ApiError(
                404,
                "FUNCION_NO_ENCONTRADA",
                "Función no encontrada",
                "No existe una función disponible con ese identificador."
            )

        butacas = listar_butacas_de_funcion(
            conexion,
            funcion_id,
            funcion["sala_id"]
        )

        butacas_libres = 0

        for butaca in butacas:
            estado = butaca["estado"]

            if estado == "disponible":
                butacas_libres += 1

            butaca["ocupada"] = estado == "ocupada"

        return {
            "funcion_id": funcion_id,
            "total_butacas": len(butacas),
            "butacas_libres": butacas_libres,
            "butacas": butacas
        }

    finally:
        conexion.close()
