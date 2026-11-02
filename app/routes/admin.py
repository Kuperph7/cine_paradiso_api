"""Rutas de administración del sistema."""
from flask import Blueprint, request, jsonify
from app.validators.auth_validators import validar_header_autorizacion
from app.validators.admin_validators import (
    validar_creacion_servicio,
    validar_actualizacion_servicio,
)
from app.services.admin_service import (
    listar_servicios,
    crear_servicio,
    modificar_servicio,
    eliminar_servicio,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/servicios", methods=["GET"])
def get_servicios():
    """Retorna la lista de todos los servicios para el administrador."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    resultado = listar_servicios(token)
    return jsonify(resultado), 200


@admin_bp.route("/servicios", methods=["POST"])
def post_servicio():
    """Registra un nuevo servicio adicional para todas las salas."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    data = request.get_json()
    validar_creacion_servicio(data)
    resultado = crear_servicio(token, data)
    return jsonify(resultado), 201


@admin_bp.route("/servicios/<int:servicio_id>", methods=["PATCH"])
def patch_servicio(servicio_id: int):
    """Modifica los datos de un servicio adicional existente."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    data = request.get_json()
    validar_actualizacion_servicio(data)
    modificar_servicio(token, servicio_id, data)
    return "", 204


@admin_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
def delete_servicio(servicio_id: int):
    """Realiza la baja lógica de un servicio desactivándolo."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    eliminar_servicio(token, servicio_id)
    return "", 204
