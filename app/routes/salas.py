from flask import Blueprint, jsonify, request

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
    requerir_administrador()
    incluir_inactivas = validar_filtros_salas(request.args)
    return jsonify(listar_salas_service(incluir_inactivas)), 200


@salas_bp.route("/salas", methods=["POST"])
def crear_sala():
    requerir_administrador()
    datos = validar_creacion_sala(request.get_json(silent=True))
    return jsonify(crear_sala_service(datos)), 201


@salas_bp.route("/salas/<int:sala_id>", methods=["PATCH"])
def actualizar_sala(sala_id):
    requerir_administrador()
    validar_sala_id(sala_id)
    cambios = validar_actualizacion_sala(request.get_json(silent=True))
    return jsonify(actualizar_sala_service(sala_id, cambios)), 200
