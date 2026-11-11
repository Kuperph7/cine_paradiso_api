
from flask import Blueprint, jsonify, request

from app.errors import es_respuesta_error, respuesta_error
from app.security import (
    es_administrador,
    obtener_identidad_opcional,
    requerir_administrador,
)

from app.services.cartelera_service import (
    consultar_peliculas,
    consultar_detalle_pelicula,
    consultar_funcion,
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
    filtros = validar_filtros_cartelera(request.args)
    if es_respuesta_error(filtros):
        return filtros
    local_id, fecha = filtros

    resultado = consultar_peliculas(local_id, fecha)
    if es_respuesta_error(resultado):
        return resultado

    return jsonify(resultado), 200


# Issue #32 - Detalle de una pelicula
@cartelera_bp.route("/cartelera/<int:pelicula_id>", methods=["GET"])
@cartelera_bp.route("/peliculas/<int:pelicula_id>", methods=["GET"])
def detalle_pelicula(pelicula_id):
    resultado = consultar_detalle_pelicula(pelicula_id)
    if es_respuesta_error(resultado):
        return resultado

    return jsonify(resultado), 200


@cartelera_bp.route("/funciones/<int:funcion_id>", methods=["GET"])
def obtener_funcion(funcion_id):
    resultado = consultar_funcion(funcion_id)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


# Issue #33 - Butacas de una funcion
@cartelera_bp.route(
    "/funciones/<int:funcion_id>/butacas",
    methods=["GET"]
)
def consultar_butacas(funcion_id):
    resultado = consultar_butacas_funcion(funcion_id)
    if es_respuesta_error(resultado):
        return resultado

    return jsonify(resultado), 200


# Gestion de funciones - Listar funciones
@cartelera_bp.route("/funciones", methods=["GET"])
def listar_funciones():
    identidad = obtener_identidad_opcional()
    if es_respuesta_error(identidad):
        return identidad
    usuario_es_administrador = es_administrador(identidad)
    filtros = validar_filtros_funciones(request.args)
    if es_respuesta_error(filtros):
        return filtros

    if filtros["estado"] is not None and not usuario_es_administrador:
        if identidad is None:
            return respuesta_error(
                401,
                "AUTENTICACION_REQUERIDA",
                "Autenticación requerida",
                "El filtro estado requiere autenticación de administrador.",
            )
        return respuesta_error(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El filtro estado es exclusivo del rol administrador.",
        )

    resultado = listar_funciones_service(filtros, usuario_es_administrador)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


# Gestion de funciones - Crear funcion
@cartelera_bp.route("/funciones", methods=["POST"])
def crear_funcion():
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad
    datos = validar_creacion_funcion(request.get_json(silent=True))
    if es_respuesta_error(datos):
        return datos
    resultado = crear_funcion_service(datos)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 201


# Gestion de funciones - Actualizar funcion
@cartelera_bp.route("/funciones/<int:funcion_id>", methods=["PATCH"])
def actualizar_funcion(funcion_id):
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad
    error = validar_funcion_id(funcion_id)
    if es_respuesta_error(error):
        return error
    cambios = validar_actualizacion_funcion(request.get_json(silent=True))
    if es_respuesta_error(cambios):
        return cambios
    resultado = actualizar_funcion_service(funcion_id, cambios)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200
