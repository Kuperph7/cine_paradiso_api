from app.db import get_db_connection
from app.errors import ApiError 

from app.repositories.servicios_repository import(
    obtener_todos_los_servicios,
    crear_servicio as crear_servicio_repository, 
    obtener_servicio_por_id,
    actualizar_servicio as actualizar_servicio_repository,
    eliminar_servicio as eliminar_servicio_repository,
)


def listar_todos_servicios():
    servicios = obtener_todos_los_servicios()
    return servicios

def crear_servicio(datos):
    nuevo_id = crear_servicio_repository(
        nombre=datos["nombre"],
        descripcion=datos["descripcion"],
        precio=datos["precio"],
        activo=True,
    )

    return {
        "id": nuevo_id,
        "nombre": datos["nombre"],
        "descripcion": datos["descripcion"],
        "precio": datos["precio"],
        "activo": True,
    }

def obtener_servicio(servicio_id):
    return obtener_servicio_por_id(servicio_id)

def actualizar_servicio(servicio_id: int, cambios: dict):
    servicio_actual = obtener_servicio_por_id(servicio_id)

    if servicio_actual is None:
        return None

    actualizar_servicio_repository(servicio_id, cambios)

    return obtener_servicio_por_id(servicio_id)

def eliminar_servicio(servicio_id):
    servicio_actual = obtener_servicio_por_id(servicio_id)

    if servicio_actual is None:
        return None

    return eliminar_servicio_repository(servicio_actual)