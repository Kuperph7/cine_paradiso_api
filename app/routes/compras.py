from flask import Blueprint, jsonify, request

from app.errors import ApiError
from app.security import obtener_identidad_opcional
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


def _identidad_autenticada():
    identidad = obtener_identidad_opcional()
    if identidad is None:
        raise ApiError(
            401,
            "AUTENTICACION_REQUERIDA",
            "Autenticación requerida",
            "Debe iniciar sesión para realizar esta operación.",
        )

    if identidad.get("rol") not in {"usuario", "cliente", "administrador"}:
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El rol autenticado no puede operar con compras.",
        )

    usuario_id = identidad.get("usuario_id")
    if (
        isinstance(usuario_id, bool)
        or not isinstance(usuario_id, int)
        or usuario_id <= 0
    ):
        raise ApiError(
            401,
            "TOKEN_INVALIDO",
            "Autenticación requerida",
            "El token no contiene un identificador de usuario válido.",
        )

    return identidad


@compras_bp.route("/compras", methods=["GET"])
def listar_compras():
    identidad = _identidad_autenticada()
    filtros = validar_filtros_compras(request.args)
    es_administrador = identidad["rol"] == "administrador"

    if filtros["usuario_id"] is not None and not es_administrador:
        raise ApiError(
            403,
            "PERMISO_DENEGADO",
            "Permiso denegado",
            "El filtro usuario_id es exclusivo del rol administrador.",
        )

    resultado = listar_compras_service(
        identidad["usuario_id"],
        es_administrador,
        filtros,
    )
    return jsonify(resultado), 200


@compras_bp.route("/compras", methods=["POST"])
def crear_compra():
    identidad = _identidad_autenticada()
    datos = validar_creacion_compra(request.get_json(silent=True))
    resultado = crear_compra_service(identidad["usuario_id"], datos)
    return jsonify(resultado), 201


@compras_bp.route("/compras/<int:compra_id>", methods=["GET"])
def obtener_compra(compra_id):
    identidad = _identidad_autenticada()
    validar_compra_id(compra_id)
    resultado = obtener_compra_service(
        compra_id,
        identidad["usuario_id"],
        identidad["rol"] == "administrador",
    )
    return jsonify(resultado), 200


@compras_bp.route("/compras/<int:compra_id>", methods=["PATCH"])
def cancelar_compra(compra_id):
    identidad = _identidad_autenticada()
    validar_compra_id(compra_id)
    datos = validar_cancelacion_compra(request.get_json(silent=True))
    resultado = cancelar_compra_service(
        compra_id,
        identidad["usuario_id"],
        identidad["rol"] == "administrador",
        datos["motivo"],
    )
    return jsonify(resultado), 200

