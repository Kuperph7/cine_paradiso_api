from flask import Blueprint, jsonify, request

from app.errors import es_respuesta_error
from app.security import requerir_acceso_compras
from app.services.reservas_service import (
    cancelar_reserva as cancelar_reserva_service,
    crear_reserva as crear_reserva_service,
    iniciar_pago as iniciar_pago_service,
    obtener_reserva as obtener_reserva_service,
    obtener_reserva_activa as obtener_reserva_activa_service,
    simular_pago as simular_pago_service,
)
from app.validators.compras_validators import (
    validar_clave_idempotencia,
    validar_creacion_reserva,
    validar_inicio_pago,
    validar_pago_simulado,
)


reservas_bp = Blueprint("reservas", __name__)


@reservas_bp.post("/funciones/<int:funcion_id>/reservas")
def crear_reserva(funcion_id):
    identidad = requerir_acceso_compras()
    if es_respuesta_error(identidad):
        return identidad
    datos = validar_creacion_reserva(request.get_json(silent=True))
    if es_respuesta_error(datos):
        return datos
    resultado = crear_reserva_service(
        identidad["usuario_id"],
        funcion_id,
        datos["butaca_ids"],
    )
    if es_respuesta_error(resultado):
        return resultado
    reserva, creada = resultado
    return jsonify(reserva), 201 if creada else 200


@reservas_bp.get("/reservas/<string:reserva_id>")
def obtener_reserva(reserva_id):
    identidad = requerir_acceso_compras()
    if es_respuesta_error(identidad):
        return identidad
    resultado = obtener_reserva_service(reserva_id, identidad["usuario_id"])
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@reservas_bp.get("/reservas/activa")
def obtener_reserva_activa():
    identidad = requerir_acceso_compras()
    if es_respuesta_error(identidad):
        return identidad
    resultado = obtener_reserva_activa_service(identidad["usuario_id"])
    return jsonify({"reserva": resultado}), 200


@reservas_bp.delete("/reservas/<string:reserva_id>")
def cancelar_reserva(reserva_id):
    identidad = requerir_acceso_compras()
    if es_respuesta_error(identidad):
        return identidad
    resultado = cancelar_reserva_service(reserva_id, identidad["usuario_id"])
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@reservas_bp.post("/reservas/<string:reserva_id>/pagos")
def iniciar_pago(reserva_id):
    identidad = requerir_acceso_compras()
    if es_respuesta_error(identidad):
        return identidad
    idempotencia = validar_clave_idempotencia(
        request.headers.get("Idempotency-Key")
    )
    if es_respuesta_error(idempotencia):
        return idempotencia
    datos = validar_inicio_pago(request.get_json(silent=True))
    if es_respuesta_error(datos):
        return datos
    resultado = iniciar_pago_service(
        reserva_id,
        identidad["usuario_id"],
        datos,
        idempotencia,
    )
    if es_respuesta_error(resultado):
        return resultado
    reserva, creada = resultado
    return jsonify(reserva), 202 if creada else 200


@reservas_bp.post("/reservas/<string:reserva_id>/pagos/simular")
def simular_pago(reserva_id):
    identidad = requerir_acceso_compras()
    if es_respuesta_error(identidad):
        return identidad
    datos = validar_pago_simulado(request.get_json(silent=True))
    if es_respuesta_error(datos):
        return datos
    resultado = simular_pago_service(
        reserva_id,
        identidad["usuario_id"],
        datos["resultado"],
    )
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200
