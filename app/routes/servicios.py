from flask import Blueprint, jsonify, request

from app.services.servicios_service import (
    listar_todos_servicios,
    crear_servicio as crear_servicio_service,
    obtener_servicio as obtener_servicio_service,
    actualizar_servicio as actualizar_servicio_service,
    eliminar_servicio as eliminar_servicio_service,
)

servicios_bp = Blueprint("servicios", __name__)

@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    servicios = listar_todos_servicios()
    return jsonify(servicios), 200

@servicios_bp.route("/servicios", methods=["POST"])
def crear_servicio():
    datos_recibidos = request.get_json(silent=True)
    servicio_creado = crear_servicio_service(datos_recibidos)
    return jsonify(servicio_creado), 201

@servicios_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
def obtener_servicio(servicio_id):
    servicio = obtener_servicio_service(servicio_id)

    if servicio is None:
        return jsonify({"error": "Servicio no encontrado"}), 404

    return jsonify(servicio), 200

@servicios_bp.route("/servicios/<int:servicio_id>", methods=["PATCH"])
def actualizar_servicio(servicio_id):

    cambios = request.get_json(silent=True)
    servicio = actualizar_servicio_service(servicio_id, cambios)

    if servicio is None:
        return jsonify({"error": "Servicio no encontrado"}), 404

    return jsonify(servicio), 200

@servicios_bp.route("/servicios/<int:servicio_id>", methods=["DELETE"])
def eliminar_servicio(servicio_id):
    eliminado = eliminar_servicio_service(servicio_id)

    if not eliminado:
        return jsonify({"error": "Servicio no encontrado"}), 404

    return "", 204

