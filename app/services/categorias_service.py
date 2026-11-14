"""Servicios del catálogo de categorías de películas."""

from app.db import get_db_connection
from app.repositories.categorias_repository import listar_categorias


def consultar_categorias():
    conexion = get_db_connection()

    try:
        categorias = listar_categorias(conexion)
        return {"categorias": categorias}
    finally:
        conexion.close()