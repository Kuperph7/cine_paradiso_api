"""Validaciones de las operaciones administrativas."""
from app.errors import ApiError


def validar_creacion_servicio(data: dict):
    """Valida los campos obligatorios y tipos para crear un servicio."""
    if not data or not isinstance(data, dict):
        raise ApiError(400, "ERROR_VALIDACION", "Datos inválidos", "El cuerpo de la solicitud debe ser un JSON válido.")

    nombre = data.get("nombre")
    if not nombre or not isinstance(nombre, str) or not nombre.strip():
        raise ApiError(400, "ERROR_VALIDACION", "Nombre requerido", "El campo 'nombre' es obligatorio y no puede estar vacío.")

    precio = data.get("precio")
    if precio is None or not isinstance(precio, int) or precio < 0:
        raise ApiError(400, "ERROR_VALIDACION", "Precio inválido", "El campo 'precio' debe ser un número entero mayor o igual a 0.")

    descripcion = data.get("descripcion")
    if descripcion is not None and not isinstance(descripcion, str):
        raise ApiError(400, "ERROR_VALIDACION", "Descripción inválida", "El campo 'descripcion' debe ser una cadena de texto.")


def validar_actualizacion_servicio(data: dict):
    """Valida los campos a modificar de un servicio existente."""
    if not data or not isinstance(data, dict):
        raise ApiError(400, "ERROR_VALIDACION", "Datos inválidos", "El cuerpo de la solicitud debe ser un JSON válido.")

    campos_validos = {"nombre", "descripcion", "precio"}
    if not any(campo in data for campo in campos_validos):
        raise ApiError(400, "ERROR_VALIDACION", "Datos vacíos", "Debe proporcionar al menos un campo válido para actualizar.")

    if "nombre" in data:
        nombre = data["nombre"]
        if not isinstance(nombre, str) or not nombre.strip():
            raise ApiError(400, "ERROR_VALIDACION", "Nombre inválido", "El campo 'nombre' no puede estar vacío.")

    if "precio" in data:
        precio = data["precio"]
        if not isinstance(precio, int) or precio < 0:
            raise ApiError(400, "ERROR_VALIDACION", "Precio inválido", "El campo 'precio' debe ser un número entero mayor o igual a 0.")

    if "descripcion" in data:
        descripcion = data["descripcion"]
        if not isinstance(descripcion, str):
            raise ApiError(400, "ERROR_VALIDACION", "Descripción inválida", "El campo 'descripcion' debe ser una cadena de texto.")
