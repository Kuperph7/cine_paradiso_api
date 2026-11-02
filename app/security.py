"""Autorización JWT necesaria para los endpoints protegidos."""

import jwt
from flask import current_app, request

from app.errors import ApiError


def _error_no_autenticado(descripcion):
    raise ApiError(401, "TOKEN_INVALIDO", "Autenticación requerida", descripcion)


def obtener_identidad_opcional():
    autorizacion = request.headers.get("Authorization")
    if autorizacion is None:
        return None

    partes = autorizacion.split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        _error_no_autenticado("Use el encabezado Authorization con el esquema Bearer.")

    secreto = current_app.config.get("SECRET_KEY")
    if not secreto:
        _error_no_autenticado("No fue posible validar el token de acceso.")

    try:
        return jwt.decode(partes[1], secreto, algorithms=["HS256"])
    except jwt.PyJWTError:
        _error_no_autenticado("El token de acceso es inválido o expiró.")


def requerir_administrador():
    identidad = obtener_identidad_opcional()
    if identidad is None:
        _error_no_autenticado("Debe iniciar sesión para realizar esta operación.")
    if identidad.get("rol") != "administrador":
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "La operación requiere rol administrador.",
        )
    return identidad
