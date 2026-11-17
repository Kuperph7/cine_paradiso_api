"""Reglas de negocio del catálogo de servicios adicionales."""

from mysql.connector import IntegrityError

from app.errors import respuesta_error
from app.repositories import servicios_repository


def obtener_config_estacionamiento():
    """Parámetros del estacionamiento definidos localmente (sin variables globales)."""
    return {
        "servicio_id": 9,
        "capacidad_maxima": 20,
        # 3 horas de ocupación (3 * 3600 = 10800 segundos).
        "duracion_segundos": 3 * 3600,
    }


def _calcular_disponibles_estacionamiento(funcion_id=None):
    config = obtener_config_estacionamiento()
    ocupados = servicios_repository.obtener_estacionamientos_ocupados(
        config["servicio_id"],
        config["duracion_segundos"],
        funcion_id=funcion_id,
    )
    return max(0, config["capacidad_maxima"] - ocupados)


def _serializar_servicio(
    servicio,
    disponibles_estacionamiento=None,
    funcion_id=None,
):
    """Adapta los tipos de MySQL al esquema Servicio de Swagger."""
    config = obtener_config_estacionamiento()
    resultado = {
        "id": int(servicio["id"]),
        "nombre": servicio["nombre"],
        "descripcion": servicio["descripcion"] or "",
        "precio": int(servicio["precio"]),
        "activo": bool(servicio["activo"]),
    }
    if int(servicio["id"]) == config["servicio_id"]:
        if disponibles_estacionamiento is None:
            disponibles_estacionamiento = _calcular_disponibles_estacionamiento(
                funcion_id=funcion_id
            )
        resultado["disponibles"] = disponibles_estacionamiento
        resultado["capacidad_maxima"] = config["capacidad_maxima"]
        resultado["duracion_segundos"] = config["duracion_segundos"]
    return resultado


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


def listar_servicios(incluir_inactivos=False, funcion_id=None):
    """Lista el catálogo público o el catálogo administrativo completo."""
    config = obtener_config_estacionamiento()
    servicios_repository.asegurar_servicio_estacionamiento(
        config["servicio_id"]
    )
    servicios = servicios_repository.obtener_todos_los_servicios(
        incluir_inactivos=incluir_inactivos
    )
    disponibles = _calcular_disponibles_estacionamiento(funcion_id=funcion_id)
    return {
        "servicios": [
            _serializar_servicio(servicio, disponibles, funcion_id=funcion_id)
            for servicio in servicios
        ]
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

    servicios_repository.eliminar_servicio(servicio_id)
    return None
