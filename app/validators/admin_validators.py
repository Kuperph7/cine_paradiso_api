"""Validaciones de las operaciones administrativas."""

from app.validators.common import (
    validate_choice,
    validate_date_range,
    validate_non_negative_number,
    validate_positive_integer,
)


FUNCTION_STATES = frozenset({"programada", "cancelada"})
DEFAULT_FUNCTION_STATE = "programada"


def validate_function_state(value):
    return validate_choice(value, "estado", FUNCTION_STATES)


def validate_function_price(value):
    return validate_non_negative_number(value, "precio")


def validate_service_price(value):
    return validate_non_negative_number(value, "precio")


def validate_room_dimensions(rows, seats_per_row):
    return (
        validate_positive_integer(rows, "filas"),
        validate_positive_integer(seats_per_row, "butacas_por_fila"),
    )


def validate_movie_duration(value):
    return validate_positive_integer(value, "duracion_minutos")


def validate_movie_availability(start, end):
    return validate_date_range(
        start,
        end,
        "disponible_desde",
        "disponible_hasta",
    )

