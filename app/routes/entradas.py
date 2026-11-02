"""Rutas de consulta de entradas del cliente."""
from flask import Blueprint, request, jsonify
from app.validators.auth_validators import validar_header_autorizacion
from app.services.entradas_service import listar_mis_entradas, consultar_entrada

entradas_bp = Blueprint("entradas", __name__)


@entradas_bp.route("/mis-entradas", methods=["GET"])
def get_mis_entradas():
    """Lista todas las entradas del cliente autenticado con su función, butaca y estado."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    resultado = listar_mis_entradas(token)
    return jsonify(resultado), 200


@entradas_bp.route("/entradas/<int:entrada_id>", methods=["GET"])
def get_entrada(entrada_id: int):
    """Devuelve el detalle de una entrada específica que pertenezca al cliente autenticado."""
    token = validar_header_autorizacion(request.headers.get("Authorization"))
    resultado = consultar_entrada(token, entrada_id)
    return jsonify(resultado), 200
