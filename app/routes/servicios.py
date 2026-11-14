"""Endpoints contractuales del catálogo de servicios adicionales."""

from flask import Blueprint, jsonify, request

from app.errors import es_respuesta_error, respuesta_error
from app.security import (
    es_administrador,
    obtener_identidad_opcional,
    requerir_administrador,
)
from app.services.servicios_service import (
    actualizar_servicio as actualizar_servicio_service,
    crear_servicio as crear_servicio_service,
    eliminar_servicio as eliminar_servicio_service,
    listar_servicios as listar_servicios_service,
    obtener_servicio as obtener_servicio_service,
)
from app.validators.servicios_validators import (
    validar_actualizacion_servicio,
    validar_creacion_servicio,
    validar_filtro_incluir_inactivos,
    validar_servicio_id,
)


servicios_bp = Blueprint("servicios", __name__)


@servicios_bp.get("/servicios")
def listar_servicios():
    identidad = obtener_identidad_opcional()
    if es_respuesta_error(identidad):
        return identidad

    incluir_inactivos = validar_filtro_incluir_inactivos(request.args)
    if es_respuesta_error(incluir_inactivos):
        return incluir_inactivos
    if incluir_inactivos and not es_administrador(identidad):
        return respuesta_error(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El filtro incluir_inactivos es exclusivo del administrador.",
        )

    resultado = listar_servicios_service(
        incluir_inactivos=incluir_inactivos
    )
    return jsonify(resultado), 200


@servicios_bp.post("/servicios")
def crear_servicio():
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad

    datos = validar_creacion_servicio(request.get_json(silent=True))
    if es_respuesta_error(datos):
        return datos

    resultado = crear_servicio_service(datos)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 201


@servicios_bp.get("/servicios/<int:servicio_id>")
def obtener_servicio(servicio_id):
    identidad = obtener_identidad_opcional()
    if es_respuesta_error(identidad):
        return identidad

    servicio_id = validar_servicio_id(servicio_id)
    if es_respuesta_error(servicio_id):
        return servicio_id

    resultado = obtener_servicio_service(
        servicio_id,
        permitir_inactivo=es_administrador(identidad),
    )
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@servicios_bp.patch("/servicios/<int:servicio_id>")
def actualizar_servicio(servicio_id):
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad

    servicio_id = validar_servicio_id(servicio_id)
    if es_respuesta_error(servicio_id):
        return servicio_id
    cambios = validar_actualizacion_servicio(request.get_json(silent=True))
    if es_respuesta_error(cambios):
        return cambios

    resultado = actualizar_servicio_service(servicio_id, cambios)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@servicios_bp.delete("/servicios/<int:servicio_id>")
def eliminar_servicio(servicio_id):
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad

    servicio_id = validar_servicio_id(servicio_id)
    if es_respuesta_error(servicio_id):
        return servicio_id
    resultado = eliminar_servicio_service(servicio_id)
    if es_respuesta_error(resultado):
        return resultado
    return "", 204
