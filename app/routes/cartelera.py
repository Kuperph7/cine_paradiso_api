from flask import Blueprint, jsonify, request

from app.services.cartelera_service import (
    consultar_peliculas,
    consultar_detalle_pelicula
)
from app.validators.cartelera_validators import validar_filtros_cartelera


cartelera_bp = Blueprint("cartelera", __name__)


@cartelera_bp.route("/cartelera", methods=["GET"])
def listar_cartelera():
    local_id, fecha = validar_filtros_cartelera(request.args)

    resultado = consultar_peliculas(local_id, fecha)

    return jsonify(resultado), 200


# Issue #32 - Consultar el detalle de una película
@cartelera_bp.route("/cartelera/<int:pelicula_id>", methods=["GET"])
def detalle_pelicula(pelicula_id):
    resultado = consultar_detalle_pelicula(pelicula_id)

    return jsonify(resultado), 200
