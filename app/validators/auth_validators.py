"""Validaciones de autenticación y perfiles."""
import re

from app.errors import respuesta_error
from app.validators.common import validation_error, validate_choice


USER_ROLES = frozenset({"cliente", "administrador"})
DEFAULT_USER_ROLE = "cliente"


def validar_registro_usuario(data: dict):
    """Valida los campos necesarios para registrar un cliente."""
    if not data or not isinstance(data, dict):
        return validation_error("El cuerpo de la solicitud debe ser un JSON válido.")

    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password", "")

    if not isinstance(nombre, str) or not nombre.strip():
        return validation_error("El campo 'nombre' debe ser un texto no vacío.")

    if not isinstance(email, str) or not email.strip():
        return validation_error("El campo 'email' debe ser un texto no vacío.")

    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, email):
        return validation_error("El formato del correo electrónico no es válido.")

    if not isinstance(password, str) or len(password) < 6:
        return validation_error("La contraseña debe tener al menos 6 caracteres.")


def validar_login_usuario(data: dict):
    """Valida los campos necesarios para iniciar sesión."""
    if not data or not isinstance(data, dict):
        return validation_error("El cuerpo de la solicitud debe ser un JSON válido.")
    if (
        not isinstance(data.get("email"), str)
        or not data["email"].strip()
        or not isinstance(data.get("password"), str)
        or not data["password"]
    ):
        return validation_error("Email y contraseña son obligatorios.")


def validar_header_autorizacion(auth_header: str) -> str:
    """Valida la presencia y formato del encabezado Authorization Bearer."""
    if not auth_header:
        return respuesta_error(
            401,
            "AUTENTICACION_REQUERIDA",
            "Autenticación requerida",
            "Se requiere el encabezado Authorization.",
        )
    partes = auth_header.strip().split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return respuesta_error(
            401,
            "TOKEN_INVALIDO",
            "Token inválido",
            "El formato del token debe ser 'Bearer <token>'.",
        )
    return partes[1]


def validate_role(value):
    return validate_choice(value, "rol", USER_ROLES)
