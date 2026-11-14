"""Validaciones reutilizables para los datos recibidos por Flask."""

from decimal import Decimal

from app.errors import respuesta_error


def validation_error(description):
    return respuesta_error(
        400,
        "DATOS_INVALIDOS",
        "Los datos enviados son inválidos",
        description,
    )


def validate_choice(value, field_name, allowed_values):
    """Valida que un string pertenezca al conjunto permitido por el contrato."""
    if not isinstance(value, str) or value not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        return validation_error(
            f"El campo '{field_name}' solo admite: {allowed}"
        )
    return value


def validate_non_negative_number(value, field_name):
    """Valida importes numéricos mayores o iguales a cero."""
    if isinstance(value, bool) or not isinstance(
        value, (int, float, Decimal)
    ):
        return validation_error(f"El campo '{field_name}' debe ser numérico")
    if value < 0:
        return validation_error(
            f"El campo '{field_name}' debe ser mayor o igual a cero"
        )
    return value


def validate_positive_integer(value, field_name):
    """Valida cantidades enteras estrictamente mayores que cero."""
    if isinstance(value, bool) or not isinstance(value, int):
        return validation_error(f"El campo '{field_name}' debe ser un entero")
    if value <= 0:
        return validation_error(
            f"El campo '{field_name}' debe ser mayor que cero"
        )
    return value


def validate_date_range(start, end, start_name, end_name):
    """Valida un período cuando ambas fechas fueron informadas."""
    if start is not None and end is not None and start >= end:
        return validation_error(
            f"El campo '{start_name}' debe ser anterior a '{end_name}'"
        )
    return start, end
