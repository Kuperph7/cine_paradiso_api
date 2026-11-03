
from flask import Blueprint, jsonify, request

from app.errors import ApiError
from app.security import obtener_identidad_opcional, requerir_administrador

from app.services.cartelera_service import (
    consultar_peliculas,
    consultar_detalle_pelicula,
    consultar_butacas_funcion,
    actualizar_funcion as actualizar_funcion_service,
    crear_funcion as crear_funcion_service,
    listar_funciones as listar_funciones_service,
)

from app.validators.cartelera_validators import (
    validar_filtros_cartelera,
    validar_actualizacion_funcion,
    validar_creacion_funcion,
    validar_filtros_funciones,
    validar_funcion_id,
)


cartelera_bp = Blueprint("cartelera", __name__)


# Issue #31 - Listar cartelera
@cartelera_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    local_id, fecha = validar_filtros_cartelera(request.args)

    resultado = consultar_peliculas(local_id, fecha)

    return jsonify(resultado), 200


# Issue #32 - Detalle de una pelicula
@cartelera_bp.route("/cartelera/<int:pelicula_id>", methods=["GET"])
def detalle_pelicula(pelicula_id):
    resultado = consultar_detalle_pelicula(pelicula_id)

    return jsonify(resultado), 200


# Issue #33 - Butacas de una funcion
@cartelera_bp.route(
    "/cartelera/funciones/<int:funcion_id>/butacas",
    methods=["GET"]
)
def consultar_butacas(funcion_id):
    resultado = consultar_butacas_funcion(funcion_id)

    return jsonify(resultado), 200


# Gestion de funciones - Listar funciones
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


# Gestion de funciones - Crear funcion
@cartelera_bp.route("/funciones", methods=["POST"])
def crear_funcion():
    requerir_administrador()
    datos = validar_creacion_funcion(request.get_json(silent=True))
    return jsonify(crear_funcion_service(datos)), 201


# Gestion de funciones - Actualizar funcion
@cartelera_bp.route("/funciones/<int:funcion_id>", methods=["PATCH"])
def actualizar_funcion(funcion_id):
    requerir_administrador()
    validar_funcion_id(funcion_id)
    cambios = validar_actualizacion_funcion(request.get_json(silent=True))
    return jsonify(actualizar_funcion_service(funcion_id, cambios)), 200
