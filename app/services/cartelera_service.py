"""Servicios de cartelera, películas y funciones."""

from app.db import get_db_connection
from app.repositories.peliculas_repository import listar_peliculas


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
