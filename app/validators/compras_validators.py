"""Validaciones de compras, servicios y cancelaciones."""

from app.errors import es_respuesta_error, respuesta_error
from app.validators.common import (
    validate_choice,
    validate_non_negative_number,
    validate_positive_integer,
)


MEDIOS_PAGO = {"tarjeta", "efectivo", "transferencia"}
ESTADOS_COMPRA = {"confirmada", "cancelada"}
CAMPOS_COMPRA = {"funcion_id", "butaca_ids", "servicios", "medio_pago"}
CAMPOS_COMPRA_REQUERIDOS = {"funcion_id", "butaca_ids", "medio_pago"}
CAMPOS_CANCELACION = {"estado", "motivo"}
SEAT_STATES = frozenset({"disponible", "reservada", "ocupada"})
PURCHASE_STATES = frozenset({"confirmada", "cancelada"})
TICKET_STATES = frozenset({"emitida", "utilizada", "cancelada"})

DEFAULT_SEAT_STATE = "disponible"
DEFAULT_PURCHASE_STATE = "confirmada"
DEFAULT_TICKET_STATE = "emitida"


def _error(codigo, descripcion):
    return respuesta_error(400, codigo, "Solicitud inválida", descripcion)


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        return _error("CAMPO_INVALIDO", f"{campo} debe ser un número entero positivo.")
    return valor


def _validar_objeto(datos, campos_admitidos, requeridos):
    if not isinstance(datos, dict):
        return _error(
            "CUERPO_INVALIDO",
            "El cuerpo de la solicitud debe ser un objeto JSON.",
        )

    desconocidos = set(datos) - campos_admitidos
    if desconocidos:
        campos = ", ".join(sorted(desconocidos))
        return _error("CAMPOS_DESCONOCIDOS", f"Campos no admitidos: {campos}.")

    faltantes = requeridos - set(datos)
    if faltantes:
        campos = ", ".join(sorted(faltantes))
        return _error("CAMPOS_REQUERIDOS", f"Faltan campos requeridos: {campos}.")


def validar_creacion_compra(datos):
    error = _validar_objeto(datos, CAMPOS_COMPRA, CAMPOS_COMPRA_REQUERIDOS)
    if es_respuesta_error(error):
        return error
    resultado = dict(datos)
    funcion_id = _entero_positivo(
        resultado["funcion_id"], "funcion_id"
    )
    if es_respuesta_error(funcion_id):
        return funcion_id
    resultado["funcion_id"] = funcion_id

    butaca_ids = resultado["butaca_ids"]
    if not isinstance(butaca_ids, list) or not butaca_ids:
        return _error("BUTACAS_INVALIDAS", "butaca_ids debe contener al menos una butaca.")
    butacas_validadas = []
    for butaca_id in butaca_ids:
        butaca_validada = _entero_positivo(butaca_id, "butaca_ids")
        if es_respuesta_error(butaca_validada):
            return butaca_validada
        butacas_validadas.append(butaca_validada)
    butaca_ids = butacas_validadas
    if len(butaca_ids) != len(set(butaca_ids)):
        return _error("BUTACAS_REPETIDAS", "butaca_ids no admite identificadores repetidos.")
    resultado["butaca_ids"] = butaca_ids

    medio_pago = resultado["medio_pago"]
    if not isinstance(medio_pago, str) or medio_pago not in MEDIOS_PAGO:
        return _error(
            "MEDIO_PAGO_INVALIDO",
            "medio_pago debe ser tarjeta, efectivo o transferencia.",
        )

    servicios = resultado.get("servicios", [])
    if not isinstance(servicios, list):
        return _error("SERVICIOS_INVALIDOS", "servicios debe ser una lista.")

    servicios_validados = []
    ids_servicios = []
    for indice, servicio in enumerate(servicios):
        error = _validar_objeto(
            servicio,
            {"servicio_id", "cantidad"},
            {"servicio_id", "cantidad"},
        )
        if es_respuesta_error(error):
            return error
        servicio_id = _entero_positivo(
            servicio["servicio_id"],
            f"servicios[{indice}].servicio_id",
        )
        if es_respuesta_error(servicio_id):
            return servicio_id
        cantidad = _entero_positivo(
            servicio["cantidad"],
            f"servicios[{indice}].cantidad",
        )
        if es_respuesta_error(cantidad):
            return cantidad
        ids_servicios.append(servicio_id)
        servicios_validados.append(
            {"servicio_id": servicio_id, "cantidad": cantidad}
        )

    if len(ids_servicios) != len(set(ids_servicios)):
        return _error(
            "SERVICIOS_REPETIDOS",
            "No se puede seleccionar el mismo servicio más de una vez.",
        )
    resultado["servicios"] = servicios_validados
    return resultado


def validar_cancelacion_compra(datos):
    error = _validar_objeto(datos, CAMPOS_CANCELACION, {"estado"})
    if es_respuesta_error(error):
        return error
    if datos["estado"] != "cancelada":
        return _error("ESTADO_INVALIDO", "estado debe ser 'cancelada'.")

    motivo = datos.get("motivo")
    if motivo is not None:
        if not isinstance(motivo, str):
            return _error("MOTIVO_INVALIDO", "motivo debe ser un texto.")
        if len(motivo) > 500:
            return _error("MOTIVO_INVALIDO", "motivo no puede superar 500 caracteres.")

    return {"estado": "cancelada", "motivo": motivo}


def validar_filtros_compras(args):
    usuario_id = args.get("usuario_id")
    estado = args.get("estado")

    if usuario_id is not None:
        if not usuario_id.isdecimal():
            return _error(
                "FILTRO_INVALIDO",
                "usuario_id debe ser un número entero positivo.",
            )
        usuario_id = _entero_positivo(int(usuario_id), "usuario_id")
        if es_respuesta_error(usuario_id):
            return usuario_id

    if estado is not None and estado not in ESTADOS_COMPRA:
        return _error(
            "FILTRO_INVALIDO",
            "estado debe ser 'confirmada' o 'cancelada'.",
        )

    return {"usuario_id": usuario_id, "estado": estado}


def validar_compra_id(compra_id):
    return _entero_positivo(compra_id, "compra_id")

def validate_seat_state(value):
    return validate_choice(value, "estado", SEAT_STATES)


def validate_purchase_state(value):
    return validate_choice(value, "estado", PURCHASE_STATES)


def validate_ticket_state(value):
    return validate_choice(value, "estado", TICKET_STATES)


def validate_purchase_total(value):
    return validate_non_negative_number(value, "total")


def validate_ticket_price(value):
    return validate_non_negative_number(value, "precio")


def validate_service_line(quantity, unit_price, subtotal):
    cantidad = validate_positive_integer(quantity, "cantidad")
    if es_respuesta_error(cantidad):
        return cantidad
    precio = validate_non_negative_number(unit_price, "precio_unitario")
    if es_respuesta_error(precio):
        return precio
    total = validate_non_negative_number(subtotal, "subtotal")
    if es_respuesta_error(total):
        return total
    return cantidad, precio, total
