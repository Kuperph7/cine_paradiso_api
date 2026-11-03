"""Servicios administrativos y estadísticas."""
from flask import current_app
import jwt
from mysql.connector import IntegrityError

from app.db import get_db_connection
from app.errors import ApiError
from app.integrations.peliculas_api import (
    PeliculasApiError,
    buscar_peliculas as buscar_en_tmdb,
)
from app.repositories import servicios_repository
from app.repositories.peliculas_repository import (
    actualizar_pelicula as guardar_cambios_pelicula,
    buscar_pelicula_por_id,
    buscar_pelicula_por_id_externo,
    crear_pelicula as insertar_pelicula,
    listar_peliculas as consultar_peliculas_repository,
)

def verificar_rol_administrador(token: str) -> dict:
    """Verifica que el token sea válido y pertenezca a un usuario administrador."""
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRADO", "Sesión expirada", "El token ha expirado. Inicie sesión nuevamente.")
    except jwt.InvalidTokenError:
        raise ApiError(401, "TOKEN_INVALIDO", "Token inválido", "El token de autenticación no es válido.")

    if payload.get("rol") != "administrador":
        raise ApiError(403, "ACCESO_DENEGADO", "Sin permisos", "Se requieren permisos de administrador.")

    return payload


def listar_servicios(token: str) -> dict:
    """Lista todos los servicios adicionales verificando permisos de administrador."""
    verificar_rol_administrador(token)
    servicios = servicios_repository.obtener_todos_los_servicios()
    for servicio in servicios:
        servicio["activo"] = bool(servicio["activo"])
    return {"servicios": servicios}


def crear_servicio(token: str, data: dict) -> dict:
    """Crea un nuevo servicio adicional verificando que no exista duplicación."""
    verificar_rol_administrador(token)
    nombre = data["nombre"].strip()
    if servicios_repository.obtener_servicio_por_nombre(nombre):
        raise ApiError(409, "CONFLICTO_SERVICIO", "Servicio existente", "Ya existe un servicio con ese nombre.")

    descripcion = data.get("descripcion", "").strip()
    precio = data["precio"]
    nuevo_id = servicios_repository.crear_servicio(nombre, descripcion, precio, activo=True)
    return {
        "id": nuevo_id,
        "mensaje": "Servicio creado exitosamente"
    }


def modificar_servicio(token: str, servicio_id: int, data: dict):
    """Actualiza la información de un servicio verificando su existencia."""
    verificar_rol_administrador(token)
    servicio = servicios_repository.obtener_servicio_por_id(servicio_id)
    if not servicio:
        raise ApiError(404, "SERVICIO_NO_ENCONTRADO", "Servicio no encontrado", "El servicio especificado no existe.")

    campos = {}
    if "nombre" in data:
        campos["nombre"] = data["nombre"].strip()
    if "descripcion" in data:
        campos["descripcion"] = data["descripcion"].strip()
    if "precio" in data:
        campos["precio"] = data["precio"]

    if campos:
        servicios_repository.actualizar_servicio(servicio_id, campos)


def eliminar_servicio(token: str, servicio_id: int):
    """Desactiva lógicamente un servicio verificando su existencia."""
    verificar_rol_administrador(token)
    servicio = servicios_repository.obtener_servicio_por_id(servicio_id)
    if not servicio:
        raise ApiError(404, "SERVICIO_NO_ENCONTRADO", "Servicio no encontrado", "El servicio especificado no existe.")

    servicios_repository.dar_de_baja_servicio(servicio_id)




def _serializar_pelicula(pelicula):
    resultado = dict(pelicula)
    if resultado.get("id_externo") is not None:
        resultado["id_externo"] = int(resultado["id_externo"])
    resultado["duracion_minutos"] = int(resultado["duracion_minutos"])
    resultado["activa"] = bool(resultado["activa"])
    return resultado


def listar_peliculas(filtros, es_administrador=False):
    conexion = get_db_connection()
    try:
        peliculas = consultar_peliculas_repository(
            conexion,
            **filtros,
            solo_publicadas=not es_administrador,
        )
        return {
            "peliculas": [_serializar_pelicula(pelicula) for pelicula in peliculas]
        }
    finally:
        conexion.close()


def buscar_peliculas_externas(titulo):
    api_key = current_app.config.get("MOVIES_API_KEY")
    if not api_key:
        raise ApiError(
            503,
            "CATALOGO_NO_CONFIGURADO",
            "Catálogo externo no disponible",
            "Falta configurar MOVIES_API_KEY.",
        )

    try:
        peliculas = buscar_en_tmdb(titulo, api_key)
    except PeliculasApiError as error:
        raise ApiError(
            502,
            "ERROR_CATALOGO_EXTERNO",
            "Catálogo externo no disponible",
            "No fue posible consultar el catálogo externo.",
        ) from error

    return {"peliculas": peliculas}


def _conflicto_pelicula():
    return ApiError(
        409,
        "CONFLICTO_PELICULA",
        "No fue posible guardar la película",
        "La película entra en conflicto con los datos existentes.",
    )


def crear_pelicula(datos):
    conexion = get_db_connection()
    try:
        id_externo = datos.get("id_externo")
        if id_externo is not None and buscar_pelicula_por_id_externo(
            conexion, id_externo
        ):
            raise ApiError(
                409,
                "PELICULA_DUPLICADA",
                "Película ya registrada",
                "Ya existe una película con ese id_externo.",
            )

        pelicula_id = insertar_pelicula(conexion, datos)
        pelicula = buscar_pelicula_por_id(conexion, pelicula_id)
        conexion.commit()
        return _serializar_pelicula(pelicula)
    except IntegrityError as error:
        conexion.rollback()
        raise _conflicto_pelicula() from error
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def actualizar_pelicula(pelicula_id, cambios):
    conexion = get_db_connection()
    try:
        pelicula = buscar_pelicula_por_id(conexion, pelicula_id)
        if pelicula is None:
            raise ApiError(
                404,
                "PELICULA_NO_ENCONTRADA",
                "Película no encontrada",
                "No existe una película con ese identificador.",
            )

        guardar_cambios_pelicula(conexion, pelicula_id, cambios)
        pelicula = buscar_pelicula_por_id(conexion, pelicula_id)
        conexion.commit()
        return _serializar_pelicula(pelicula)
    except IntegrityError as error:
        conexion.rollback()
        raise _conflicto_pelicula() from error
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

