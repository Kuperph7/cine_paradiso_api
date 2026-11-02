
from flask import Blueprint, jsonify, request

from app.errors import ApiError
from app.security import obtener_identidad_opcional

from app.services.admin_service import (
    obtener_estadisticas as obtener_estadisticas_service,
)

from app.validators.admin_validators import (
    validar_filtros_estadisticas,
)


admin_bp = Blueprint("admin", __name__)


def _identidad_administrador():
    identidad = obtener_identidad_opcional()

    if identidad is None:
        raise ApiError(
            401,
            "AUTENTICACION_REQUERIDA",
            "Autenticación requerida",
            "Debe iniciar sesión para realizar esta operación.",
        )

    if identidad.get("rol") != "administrador":
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "Esta operación requiere permisos de administrador.",
        )

    return identidad


@admin_bp.route(
    "/estadisticas",
    methods=["GET"],
)
@admin_bp.route(
    "/admin/estadisticas",
    methods=["GET"],
)
def obtener_estadisticas():
    _identidad_administrador()

    filtros = validar_filtros_estadisticas(
        request.args
    )

    resultado = obtener_estadisticas_service(
        filtros
    )

    return jsonify(resultado), 200





