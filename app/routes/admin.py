from flask import Blueprint, jsonify, request

from app.errors import ApiError
from app.security import obtener_identidad_opcional, requerir_administrador
from app.services.admin_service import (
    actualizar_pelicula as actualizar_pelicula_service,
    buscar_peliculas_externas as buscar_peliculas_externas_service,
    crear_pelicula as crear_pelicula_service,
    listar_peliculas as listar_peliculas_service,
)
from app.validators.admin_validators import (
    validar_actualizacion_pelicula,
    validar_busqueda_peliculas_externas,
    validar_creacion_pelicula,
    validar_filtros_peliculas,
    validar_pelicula_id,
)


admin_bp = Blueprint("admin", __name__)
"""Rutas de administración del sistema."""
from flask import Blueprint, request, jsonify
from app.validators.auth_validators import validar_header_autorizacion
from app.validators.admin_validators import (
    validar_creacion_servicio,
    validar_actualizacion_servicio,
    validar_entrada_qr_request,
)
from app.services.admin_service import (
    listar_servicios,
    crear_servicio,
    modificar_servicio,
    eliminar_servicio,
)
from app.services.entradas_service import validar_entrada_qr

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


@admin_bp.route("/entradas/validar", methods=["POST"])
def post_validar_entrada():
    """Verifica el QR de una entrada y la marca como utilizada si el acceso es válido."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    data = request.get_json()
    validar_entrada_qr_request(data)
    resultado = validar_entrada_qr(token, data["codigo_qr"].strip(), data["funcion_id"])
    return jsonify(resultado), 200


@admin_bp.route("/peliculas", methods=["GET"])
def listar_peliculas():
    identidad = obtener_identidad_opcional()
    es_administrador = bool(
        identidad and identidad.get("rol") == "administrador"
    )
    filtros = validar_filtros_peliculas(request.args)

    if filtros["incluir_inactivas"] and not es_administrador:
        if identidad is None:
            raise ApiError(
                401,
                "AUTENTICACION_REQUERIDA",
                "Autenticación requerida",
                "El filtro incluir_inactivas requiere autenticación "
                "de administrador.",
            )
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El filtro incluir_inactivas es exclusivo del rol administrador.",
        )

    resultado = listar_peliculas_service(filtros, es_administrador)
    return jsonify(resultado), 200


@admin_bp.route("/peliculas", methods=["POST"])
def crear_pelicula():
    requerir_administrador()
    datos = validar_creacion_pelicula(request.get_json(silent=True))
    return jsonify(crear_pelicula_service(datos)), 201


@admin_bp.route("/peliculas/externas", methods=["GET"])
def buscar_peliculas_externas():
    requerir_administrador()
    titulo = validar_busqueda_peliculas_externas(request.args)
    return jsonify(buscar_peliculas_externas_service(titulo)), 200


@admin_bp.route("/peliculas/<int:pelicula_id>", methods=["PATCH"])
def actualizar_pelicula(pelicula_id):
    requerir_administrador()
    validar_pelicula_id(pelicula_id)
    cambios = validar_actualizacion_pelicula(request.get_json(silent=True))
    return jsonify(actualizar_pelicula_service(pelicula_id, cambios)), 200

