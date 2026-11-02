from flask import Blueprint, jsonify, request

from app.errors import ApiError
from app.security import obtener_identidad_opcional, requerir_administrador
from app.services.cartelera_service import (
    actualizar_funcion as actualizar_funcion_service,
    crear_funcion as crear_funcion_service,
    listar_funciones as listar_funciones_service,
)
from app.validators.cartelera_validators import (
    validar_actualizacion_funcion,
    validar_creacion_funcion,
    validar_filtros_funciones,
    validar_funcion_id,
)


cartelera_bp = Blueprint("cartelera", __name__)


@cartelera_bp.route("/funciones", methods=["GET"])
def listar_funciones():
    identidad = obtener_identidad_opcional()
    es_administrador = bool(
        identidad and identidad.get("rol") == "administrador"
    )
    filtros = validar_filtros_funciones(request.args)

    if filtros["estado"] is not None and not es_administrador:
        if identidad is None:
            raise ApiError(
                401,
                "AUTENTICACION_REQUERIDA",
                "Autenticación requerida",
                "El filtro estado requiere autenticación de administrador.",
            )
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El filtro estado es exclusivo del rol administrador.",
        )

    resultado = listar_funciones_service(filtros, es_administrador)
    return jsonify(resultado), 200


@cartelera_bp.route("/funciones", methods=["POST"])
def crear_funcion():
    requerir_administrador()
    datos = validar_creacion_funcion(request.get_json(silent=True))
    return jsonify(crear_funcion_service(datos)), 201


@cartelera_bp.route("/funciones/<int:funcion_id>", methods=["PATCH"])
def actualizar_funcion(funcion_id):
    requerir_administrador()
    validar_funcion_id(funcion_id)
    cambios = validar_actualizacion_funcion(request.get_json(silent=True))
    return jsonify(actualizar_funcion_service(funcion_id, cambios)), 200

