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

