"""Servicios administrativos y estadísticas."""
from flask import current_app
import jwt
from app.errors import ApiError
from app.repositories import servicios_repository


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
