"""Validaciones de compras, servicios y cancelaciones."""

from app.validators.common import (
    validate_choice,
    validate_non_negative_number,
    validate_positive_integer,
)


SEAT_STATES = frozenset({"disponible", "reservada", "ocupada"})
PURCHASE_STATES = frozenset({"confirmada", "cancelada"})
TICKET_STATES = frozenset({"emitida", "utilizada", "cancelada"})

DEFAULT_SEAT_STATE = "disponible"
DEFAULT_PURCHASE_STATE = "confirmada"
DEFAULT_TICKET_STATE = "emitida"


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
    return (
        validate_positive_integer(quantity, "cantidad"),
        validate_non_negative_number(unit_price, "precio_unitario"),
        validate_non_negative_number(subtotal, "subtotal"),
    )

