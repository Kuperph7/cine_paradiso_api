"""Validaciones de autenticación y perfiles."""
import re
from app.errors import ApiError


def validar_registro_usuario(data: dict):
    """Valida los campos necesarios para registrar un cliente."""
    if not data or not isinstance(data, dict):
        raise ApiError(400, "ERROR_VALIDACION", "Datos inválidos", "El cuerpo de la solicitud debe ser un JSON válido.")

    nombre = data.get("nombre", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not nombre:
        raise ApiError(400, "ERROR_VALIDACION", "Nombre requerido", "El campo 'nombre' no puede estar vacío.")

    if not email:
        raise ApiError(400, "ERROR_VALIDACION", "Email requerido", "El campo 'email' no puede estar vacío.")

    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        raise ApiError(400, "ERROR_VALIDACION", "Email inválido", "El formato del correo electrónico no es válido.")

    if not password or len(password) < 6:
        raise ApiError(400, "ERROR_VALIDACION", "Contraseña inválida", "La contraseña debe tener al menos 6 caracteres.")


def validar_login_usuario(data: dict):
    """Valida los campos necesarios para iniciar sesión."""
    if not data or not isinstance(data, dict):
        raise ApiError(400, "ERROR_VALIDACION", "Datos inválidos", "El cuerpo de la solicitud debe ser un JSON válido.")
    if not data.get("email") or not data.get("password"):
        raise ApiError(400, "ERROR_VALIDACION", "Datos incompletos", "Email y contraseña son obligatorios.")
