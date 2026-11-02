"""Servicios de cartelera, películas y funciones."""

from datetime import datetime
from zoneinfo import ZoneInfo

from mysql.connector import IntegrityError

from app.db import get_db_connection
from app.errors import ApiError
from app.repositories.funciones_repository import (
    actualizar_funcion as guardar_cambios_funcion,
    buscar_funcion_por_id,
    crear_funcion as insertar_funcion,
    existe_funcion_en_horario,
    listar_funciones as consultar_funciones_repository,
)
from app.repositories.peliculas_repository import buscar_pelicula_por_id
from app.repositories.salas_repository import buscar_sala_por_id


ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")


def _fecha_para_base(fecha):
    return fecha.astimezone(ZONA_HORARIA).replace(tzinfo=None)


def _serializar_funcion(funcion):
    resultado = dict(funcion)
    fecha_hora = resultado["fecha_hora"]
    if isinstance(fecha_hora, datetime):
        if fecha_hora.tzinfo is None:
            fecha_hora = fecha_hora.replace(tzinfo=ZONA_HORARIA)
        else:
            fecha_hora = fecha_hora.astimezone(ZONA_HORARIA)
        resultado["fecha_hora"] = fecha_hora.isoformat()
    resultado["precio"] = int(resultado["precio"])
    return resultado


def _validar_fecha_futura(fecha_hora):
    if fecha_hora <= datetime.now(fecha_hora.tzinfo):
        raise ApiError(
            400,
            "FECHA_HORA_INVALIDA",
            "Fecha y hora inválidas",
            "La función debe programarse para una fecha y hora futuras.",
        )


def _validar_pelicula(conexion, pelicula_id):
    pelicula = buscar_pelicula_por_id(conexion, pelicula_id)
    if pelicula is None:
        raise ApiError(
            404,
            "PELICULA_NO_ENCONTRADA",
            "Película no encontrada",
            "No existe una película con ese identificador.",
        )
    if not pelicula["activa"]:
        raise ApiError(
            409,
            "PELICULA_INACTIVA",
            "Película inactiva",
            "No se puede programar una función para una película inactiva.",
        )


def _validar_sala(conexion, sala_id):
    sala = buscar_sala_por_id(conexion, sala_id)
    if sala is None:
        raise ApiError(
            404,
            "SALA_NO_ENCONTRADA",
            "Sala no encontrada",
            "No existe una sala con ese identificador.",
        )
    if not sala["activa"]:
        raise ApiError(
            409,
            "SALA_INACTIVA",
            "Sala inactiva",
            "No se puede programar una función en una sala inactiva.",
        )


def _validar_horario(conexion, sala_id, fecha_hora, excluir_id=None):
    if existe_funcion_en_horario(conexion, sala_id, fecha_hora, excluir_id):
        raise ApiError(
            409,
            "HORARIO_NO_DISPONIBLE",
            "Horario no disponible",
            "La sala ya tiene una función registrada en esa fecha y hora.",
        )


def _conflicto_integridad():
    return ApiError(
        409,
        "CONFLICTO_FUNCION",
        "No fue posible guardar la función",
        "La función entra en conflicto con los datos existentes.",
    )


def listar_funciones(filtros, es_administrador=False):
    conexion = get_db_connection()
    try:
        filtros_db = dict(filtros)
        for campo in ("desde", "hasta"):
            if filtros_db[campo] is not None:
                filtros_db[campo] = _fecha_para_base(filtros_db[campo])

        funciones = consultar_funciones_repository(
            conexion,
            **filtros_db,
            solo_publicadas=not es_administrador,
        )
        return {"funciones": [_serializar_funcion(funcion) for funcion in funciones]}
    finally:
        conexion.close()


def crear_funcion(datos):
    conexion = get_db_connection()
    try:
        _validar_fecha_futura(datos["fecha_hora"])
        _validar_pelicula(conexion, datos["pelicula_id"])
        _validar_sala(conexion, datos["sala_id"])

        datos_db = dict(datos)
        datos_db["fecha_hora"] = _fecha_para_base(datos["fecha_hora"])
        _validar_horario(conexion, datos_db["sala_id"], datos_db["fecha_hora"])

        funcion_id = insertar_funcion(conexion, datos_db)
        funcion = buscar_funcion_por_id(conexion, funcion_id)
        conexion.commit()
        return _serializar_funcion(funcion)
    except IntegrityError as error:
        conexion.rollback()
        raise _conflicto_integridad() from error
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def actualizar_funcion(funcion_id, cambios):
    conexion = get_db_connection()
    try:
        funcion_actual = buscar_funcion_por_id(conexion, funcion_id, bloquear=True)
        if funcion_actual is None:
            raise ApiError(
                404,
                "FUNCION_NO_ENCONTRADA",
                "Función no encontrada",
                "No existe una función con ese identificador.",
            )

        datos_finales = dict(funcion_actual)
        datos_finales.update(cambios)

        reprograma = bool(
            {"pelicula_id", "sala_id", "fecha_hora"} & set(cambios)
        ) or cambios.get("estado") == "programada"
        if reprograma:
            fecha_validada = cambios.get("fecha_hora")
            if fecha_validada is None:
                fecha_validada = funcion_actual["fecha_hora"]
                if fecha_validada.tzinfo is None:
                    fecha_validada = fecha_validada.replace(tzinfo=ZONA_HORARIA)
            _validar_fecha_futura(fecha_validada)
            _validar_pelicula(conexion, datos_finales["pelicula_id"])
            _validar_sala(conexion, datos_finales["sala_id"])

        cambios_db = dict(cambios)
        if "fecha_hora" in cambios_db:
            cambios_db["fecha_hora"] = _fecha_para_base(cambios_db["fecha_hora"])
            datos_finales["fecha_hora"] = cambios_db["fecha_hora"]

        cambio_de_horario = bool({"sala_id", "fecha_hora"} & set(cambios_db))
        if cambio_de_horario or cambios.get("estado") == "programada":
            _validar_horario(
                conexion,
                datos_finales["sala_id"],
                datos_finales["fecha_hora"],
                excluir_id=funcion_id,
            )

        guardar_cambios_funcion(conexion, funcion_id, cambios_db)
        funcion = buscar_funcion_por_id(conexion, funcion_id)
        conexion.commit()
        return _serializar_funcion(funcion)
    except IntegrityError as error:
        conexion.rollback()
        raise _conflicto_integridad() from error
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

