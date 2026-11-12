"""Reglas de negocio del catálogo de servicios adicionales."""

from mysql.connector import IntegrityError

from app.errors import respuesta_error
from app.repositories import servicios_repository


def _serializar_servicio(servicio):
    """Adapta los tipos de MySQL al esquema Servicio de Swagger."""
    return {
        "id": int(servicio["id"]),
        "nombre": servicio["nombre"],
        "descripcion": servicio["descripcion"] or "",
        "precio": int(servicio["precio"]),
        "activo": bool(servicio["activo"]),
    }


def _servicio_no_encontrado():
    return respuesta_error(
        404,
        "SERVICIO_NO_ENCONTRADO",
        "Servicio no encontrado",
        "El servicio especificado no existe.",
    )


def _servicio_duplicado():
    return respuesta_error(
        409,
        "CONFLICTO_SERVICIO",
        "Servicio existente",
        "Ya existe un servicio con ese nombre.",
    )


def listar_servicios(incluir_inactivos=False):
    """Lista el catálogo público o el catálogo administrativo completo."""
    servicios = servicios_repository.obtener_todos_los_servicios(
        incluir_inactivos=incluir_inactivos
    )
    return {
        "servicios": [_serializar_servicio(servicio) for servicio in servicios]
    }


def obtener_servicio(servicio_id, permitir_inactivo=False):
    servicio = servicios_repository.obtener_servicio_por_id(servicio_id)
    if servicio is None or (not servicio["activo"] and not permitir_inactivo):
        return _servicio_no_encontrado()
    return _serializar_servicio(servicio)


def crear_servicio(datos):
    nombre = datos["nombre"]
    if servicios_repository.obtener_servicio_por_nombre(nombre):
        return _servicio_duplicado()

    try:
        servicio_id = servicios_repository.crear_servicio(
            nombre,
            datos.get("descripcion", ""),
            datos["precio"],
            activo=True,
        )
    except IntegrityError:
        return _servicio_duplicado()

    servicio = servicios_repository.obtener_servicio_por_id(servicio_id)
    return _serializar_servicio(servicio)


def actualizar_servicio(servicio_id, cambios):
    servicio = servicios_repository.obtener_servicio_por_id(servicio_id)
    if servicio is None:
        return _servicio_no_encontrado()

    nombre = cambios.get("nombre")
    if nombre is not None:
        existente = servicios_repository.obtener_servicio_por_nombre(nombre)
        if existente is not None and int(existente["id"]) != servicio_id:
            return _servicio_duplicado()

    try:
        servicios_repository.actualizar_servicio(servicio_id, cambios)
    except IntegrityError:
        return _servicio_duplicado()

    actualizado = servicios_repository.obtener_servicio_por_id(servicio_id)
    return _serializar_servicio(actualizado)


def eliminar_servicio(servicio_id):
    servicio = servicios_repository.obtener_servicio_por_id(servicio_id)
    if servicio is None:
        return _servicio_no_encontrado()

    servicios_repository.dar_de_baja_servicio(servicio_id)
    return None
