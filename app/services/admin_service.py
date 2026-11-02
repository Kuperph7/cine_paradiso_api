"""Servicios administrativos y estadísticas."""

from app.db import get_db_connection

from app.repositories.estadisticas_repository import (
    obtener_ocupacion_por_funcion,
    obtener_ocupacion_por_pelicula,
    obtener_ventas_por_genero,
    obtener_ventas_por_franja,
    obtener_total_cancelaciones,
)


def _calcular_porcentaje(vendidas, capacidad):
    if capacidad <= 0:
        return 0.0

    return round((vendidas / capacidad) * 100, 2)


def _serializar_ocupacion_funcion(funcion):
    vendidas = int(funcion["butacas_vendidas"])
    capacidad = int(funcion["capacidad"])

    return {
        "funcion_id": int(funcion["funcion_id"]),
        "butacas_vendidas": vendidas,
        "capacidad": capacidad,
        "porcentaje": _calcular_porcentaje(
            vendidas,
            capacidad,
        ),
    }


def _serializar_ocupacion_pelicula(pelicula):
    vendidas = int(pelicula["butacas_vendidas"])
    capacidad = int(pelicula["capacidad_total_funciones"] or 0)

    return {
        "pelicula_id": int(pelicula["pelicula_id"]),
        "butacas_vendidas": vendidas,
        "capacidad_total_funciones": capacidad,
        "porcentaje": _calcular_porcentaje(
            vendidas,
            capacidad,
        ),
    }


def _serializar_ventas_genero(genero):
    return {
        "genero": genero["genero"],
        "total_ventas": int(genero["total_ventas"]),
    }


def _serializar_franja(franja):
    hora_inicio = int(franja["hora_inicio"])
    hora_fin = (hora_inicio + 3) % 24

    return {
        "franja": (
            f"{hora_inicio:02d}:00-{hora_fin:02d}:00"
        ),
        "entradas_vendidas": int(
            franja["entradas_vendidas"]
        ),
    }


def obtener_estadisticas(filtros):
    conexion = get_db_connection()

    try:
        ocupacion_funciones = obtener_ocupacion_por_funcion(
            conexion,
            filtros,
        )

        ocupacion_peliculas = obtener_ocupacion_por_pelicula(
            conexion,
            filtros,
        )

        ventas_generos = obtener_ventas_por_genero(
            conexion,
            filtros,
        )

        ventas_franjas = obtener_ventas_por_franja(
            conexion,
            filtros,
        )

        cancelaciones = obtener_total_cancelaciones(
            conexion,
            filtros,
        )

        return {
            "ocupacion_por_funcion": [
                _serializar_ocupacion_funcion(funcion)
                for funcion in ocupacion_funciones
            ],

            "ocupacion_por_pelicula": [
                _serializar_ocupacion_pelicula(pelicula)
                for pelicula in ocupacion_peliculas
            ],

            "ventas_por_genero": [
                _serializar_ventas_genero(genero)
                for genero in ventas_generos
            ],

            "franjas_horarias": [
                _serializar_franja(franja)
                for franja in ventas_franjas
            ],

            "cancelaciones": int(
                cancelaciones["cancelaciones"]
            ),
        }

    finally:
        conexion.close()