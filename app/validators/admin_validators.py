"""Validaciones de las operaciones administrativas."""


"""Validaciones de filtros de estadísticas."""

from datetime import datetime

from app.errors import ApiError
from zoneinfo import ZoneInfo

ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")

def _error(codigo, descripcion):
    raise ApiError(
        400,
        codigo,
        "Solicitud inválida",
        descripcion,
    )


def _validar_fecha(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        _error("FILTRO_INVALIDO", f"{campo} debe ser una fecha válida.")

    try:
        fecha = datetime.fromisoformat(valor)

        if fecha.tzinfo is None:
            raise ValueError("Falta la zona horaria.")

        return fecha.astimezone(ZONA_HORARIA).replace(tzinfo=None)

    except ValueError:
        _error(
            "FILTRO_INVALIDO",
            f"{campo} debe tener formato ISO 8601 con zona horaria.",
        )


def validar_filtros_estadisticas(args):
    desde = args.get("desde")
    hasta = args.get("hasta")

    if (desde is None) != (hasta is None):
        _error(
            "FILTROS_INCOMPLETOS",
            "Los parámetros desde y hasta deben enviarse juntos.",
        )

    if desde is None:
        return {
            "desde": None,
            "hasta": None,
        }

    fecha_desde = _validar_fecha(desde, "desde")
    fecha_hasta = _validar_fecha(hasta, "hasta")

    if fecha_desde > fecha_hasta:
        _error(
            "RANGO_FECHAS_INVALIDO",
            "La fecha desde no puede ser posterior a hasta.",
        )

    return {
        "desde": fecha_desde,
        "hasta": fecha_hasta,
    }
