"""Emisión, validación y autorización de tokens JWT."""

from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app, request

from app.errors import es_respuesta_error, respuesta_error


ALGORITMO_JWT = "HS256"
DURACION_TOKEN = timedelta(hours=4)
ROL_USUARIO = "usuario"
ROL_CLIENTE = "cliente"
ROL_ADMINISTRADOR = "administrador"
ROLES_ENTRADAS = (ROL_CLIENTE, ROL_ADMINISTRADOR)
ROLES_COMPRAS = (ROL_USUARIO, ROL_CLIENTE, ROL_ADMINISTRADOR)


def _error_no_autenticado(descripcion):
    return respuesta_error(
        401,
        "TOKEN_INVALIDO",
        "Autenticación requerida",
        descripcion,
    )


def _obtener_secreto():
    secreto = current_app.config.get("SECRET_KEY")
    if not secreto:
        return _error_no_autenticado("No fue posible validar el token de acceso.")
    return secreto


def _extraer_token_bearer(autorizacion):
    partes = autorizacion.strip().split()
    if len(partes) != 2 or partes[0].lower() != "bearer":
        return _error_no_autenticado(
            "Use el encabezado Authorization con el esquema Bearer."
        )
    return partes[1]


def generar_token_acceso(usuario):
    """Genera el JWT de acceso de un usuario autenticado."""
    payload = {
        "usuario_id": usuario["id"],
        "email": usuario["email"],
        "rol": usuario["rol"],
        "exp": datetime.now(timezone.utc) + DURACION_TOKEN,
    }
    secreto = _obtener_secreto()
    if es_respuesta_error(secreto):
        return secreto
    return jwt.encode(
        payload,
        secreto,
        algorithm=ALGORITMO_JWT,
    )


def decodificar_token(token):
    """Valida la firma y vencimiento de un JWT y devuelve su identidad."""
    secreto = _obtener_secreto()
    if es_respuesta_error(secreto):
        return secreto
    try:
        return jwt.decode(
            token,
            secreto,
            algorithms=[ALGORITMO_JWT],
        )
    except jwt.ExpiredSignatureError:
        return respuesta_error(
            401,
            "TOKEN_EXPIRADO",
            "Sesión expirada",
            "El token ha expirado. Inicie sesión nuevamente.",
        )
    except jwt.InvalidTokenError:
        return respuesta_error(
            401,
            "TOKEN_INVALIDO",
            "Token inválido",
            "El token de autenticación no es válido.",
        )


def obtener_identidad_opcional():
    """Obtiene la identidad del request o ``None`` si no se envió un token."""
    autorizacion = request.headers.get("Authorization")
    if autorizacion is None:
        return None
    token = _extraer_token_bearer(autorizacion)
    if es_respuesta_error(token):
        return token
    return decodificar_token(token)


def requerir_usuario_autenticado(*roles_permitidos):
    """Exige una identidad con usuario válido y, opcionalmente, un rol permitido."""
    identidad = obtener_identidad_opcional()
    if es_respuesta_error(identidad):
        return identidad
    if identidad is None:
        return respuesta_error(
            401,
            "AUTENTICACION_REQUERIDA",
            "Autenticación requerida",
            "Debe iniciar sesión para realizar esta operación.",
        )

    usuario_id = identidad.get("usuario_id")
    if (
        isinstance(usuario_id, bool)
        or not isinstance(usuario_id, int)
        or usuario_id <= 0
    ):
        return respuesta_error(
            401,
            "TOKEN_INVALIDO",
            "Autenticación requerida",
            "El token no contiene un identificador de usuario válido.",
        )

    if roles_permitidos and identidad.get("rol") not in roles_permitidos:
        return respuesta_error(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El rol autenticado no puede realizar esta operación.",
        )

    return identidad


def requerir_acceso_entradas():
    """Exige una identidad habilitada para consultar entradas."""
    return requerir_usuario_autenticado(*ROLES_ENTRADAS)


def requerir_acceso_compras():
    """Exige una identidad habilitada para operar con compras."""
    return requerir_usuario_autenticado(*ROLES_COMPRAS)


def es_administrador(identidad):
    """Indica si una identidad ya validada tiene rol administrador."""
    return bool(identidad and identidad.get("rol") == ROL_ADMINISTRADOR)


def requerir_administrador():
    """Exige una identidad autenticada con rol administrador."""
    identidad = obtener_identidad_opcional()
    if es_respuesta_error(identidad):
        return identidad
    if identidad is None:
        return respuesta_error(
            401,
            "AUTENTICACION_REQUERIDA",
            "Autenticación requerida",
            "Debe iniciar sesión para realizar esta operación.",
        )
    if not es_administrador(identidad):
        return respuesta_error(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "La operación requiere rol administrador.",
        )
    return identidad
