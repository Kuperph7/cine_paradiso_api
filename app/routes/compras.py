from flask import Blueprint, jsonify, request

from app.errors import ApiError
from app.security import es_administrador, requerir_acceso_compras
from app.services.compras_service import (
    cancelar_compra as cancelar_compra_service,
    crear_compra as crear_compra_service,
    listar_compras as listar_compras_service,
    obtener_compra as obtener_compra_service,
)
from app.validators.compras_validators import (
    validar_cancelacion_compra,
    validar_compra_id,
    validar_creacion_compra,
    validar_filtros_compras,
)


compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras", methods=["GET"])
def listar_compras():
    identidad = requerir_acceso_compras()
    filtros = validar_filtros_compras(request.args)
    usuario_es_administrador = es_administrador(identidad)

    if filtros["usuario_id"] is not None and not usuario_es_administrador:
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El filtro usuario_id es exclusivo del rol administrador.",
        )

    resultado = listar_compras_service(
        identidad["usuario_id"],
        usuario_es_administrador,
        filtros,
    )
    return jsonify(resultado), 200


@compras_bp.route("/compras", methods=["POST"])
def crear_compra():
    identidad = requerir_acceso_compras()
    datos = validar_creacion_compra(request.get_json(silent=True))
    resultado = crear_compra_service(identidad["usuario_id"], datos)
    return jsonify(resultado), 201


@compras_bp.route("/compras/<int:compra_id>", methods=["GET"])
def obtener_compra(compra_id):
    identidad = requerir_acceso_compras()
    validar_compra_id(compra_id)
    resultado = obtener_compra_service(
        compra_id,
        identidad["usuario_id"],
        es_administrador(identidad),
    )
    return jsonify(resultado), 200


@compras_bp.route("/compras/<int:compra_id>", methods=["PATCH"])
def cancelar_compra(compra_id):
    identidad = requerir_acceso_compras()
    validar_compra_id(compra_id)
    datos = validar_cancelacion_compra(request.get_json(silent=True))
    resultado = cancelar_compra_service(
        compra_id,
        identidad["usuario_id"],
        es_administrador(identidad),
        datos["motivo"],
    )
    return jsonify(resultado), 200

