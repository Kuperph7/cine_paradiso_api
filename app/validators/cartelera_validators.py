"""Validaciones de cartelera y administración de funciones."""

from datetime import date
import re

from app.errors import ApiError


def validar_filtros_cartelera(args):
    local_id = args.get("local_id")
    fecha = args.get("fecha")

    if local_id is not None:
        if not local_id.isdecimal() or int(local_id) <= 0:
            raise ApiError(
                400,
                "FILTRO_INVALIDO",
                "Filtro inválido",
                "local_id debe ser un número entero positivo."
            )

        local_id = int(local_id)

    if fecha is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
            raise ApiError(
                400,
                "FECHA_INVALIDA",
                "Fecha inválida",
                "La fecha debe tener formato AAAA-MM-DD."
            )

        try:
            fecha = date.fromisoformat(fecha)
        except ValueError:
            raise ApiError(
                400,
                "FECHA_INVALIDA",
                "Fecha inválida",
                "La fecha ingresada no existe."
            )

    return local_id, fecha

