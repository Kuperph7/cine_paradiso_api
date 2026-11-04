"""Validaciones de autenticación y perfiles."""

from app.validators.common import validate_choice


USER_ROLES = frozenset({"cliente", "administrador"})
DEFAULT_USER_ROLE = "cliente"


def validate_role(value):
    return validate_choice(value, "rol", USER_ROLES)

