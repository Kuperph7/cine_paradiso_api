from flask import Blueprint, jsonify, request

from app.errors import es_respuesta_error
from app.security import requerir_administrador
from app.services.salas_service import (
    actualizar_sala as actualizar_sala_service,
    crear_sala as crear_sala_service,
    listar_salas as listar_salas_service,
)
from app.validators.salas_validators import (
    validar_actualizacion_sala,
    validar_creacion_sala,
    validar_filtros_salas,
    validar_sala_id,
)


salas_bp = Blueprint("salas", __name__)


@salas_bp.route("/salas", methods=["GET"])
def listar_salas():
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad
    incluir_inactivas = validar_filtros_salas(request.args)
    if es_respuesta_error(incluir_inactivas):
        return incluir_inactivas
    resultado = listar_salas_service(incluir_inactivas)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@salas_bp.route("/salas", methods=["POST"])
def crear_sala():
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad
    datos = validar_creacion_sala(request.get_json(silent=True))
    if es_respuesta_error(datos):
        return datos
    resultado = crear_sala_service(datos)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 201


@salas_bp.route("/salas/<int:sala_id>", methods=["PATCH"])
def actualizar_sala(sala_id):
    identidad = requerir_administrador()
    if es_respuesta_error(identidad):
        return identidad
    error = validar_sala_id(sala_id)
    if es_respuesta_error(error):
        return error
    cambios = validar_actualizacion_sala(request.get_json(silent=True))
    if es_respuesta_error(cambios):
        return cambios
    resultado = actualizar_sala_service(sala_id, cambios)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200
