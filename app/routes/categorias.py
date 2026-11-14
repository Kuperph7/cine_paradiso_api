"""Endpoints del catálogo de categorías de películas."""

from flask import Blueprint, jsonify

from app.services.categorias_service import consultar_categorias


categorias_bp = Blueprint("categorias", __name__)


# Listar categorías disponibles para los filtros y formularios.
@categorias_bp.get("/categorias")
def listar_categorias():
    resultado = consultar_categorias()
    return jsonify(resultado), 200