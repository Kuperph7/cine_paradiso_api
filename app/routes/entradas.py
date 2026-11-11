"""Rutas de consulta de entradas del cliente."""
from flask import Blueprint, jsonify
from app.errors import es_respuesta_error
from app.security import requerir_acceso_entradas
from app.services.entradas_service import listar_mis_entradas, consultar_entrada

entradas_bp = Blueprint("entradas", __name__)


@entradas_bp.route("/mis-entradas", methods=["GET"])
def get_mis_entradas():
    """Lista todas las entradas del cliente autenticado con su función, butaca y estado."""
    identidad = requerir_acceso_entradas()
    if es_respuesta_error(identidad):
        return identidad
    resultado = listar_mis_entradas(identidad["usuario_id"])
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@entradas_bp.route("/entradas/<int:entrada_id>", methods=["GET"])
def get_entrada(entrada_id: int):
    """Devuelve el detalle de una entrada específica que pertenezca al cliente autenticado."""
    identidad = requerir_acceso_entradas()
    if es_respuesta_error(identidad):
        return identidad
    resultado = consultar_entrada(identidad["usuario_id"], entrada_id)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200
