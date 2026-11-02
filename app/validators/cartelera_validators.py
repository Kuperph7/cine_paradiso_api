"""Validaciones de cartelera y administración de funciones."""

import re
from datetime import datetime

from app.errors import ApiError


ESTADOS_FUNCION = {"programada", "cancelada"}
CAMPOS_FUNCION = {
    "pelicula_id",
    "sala_id",
    "fecha_hora",
    "precio",
    "estado",
}
CAMPOS_FUNCION_REQUERIDOS = {
    "pelicula_id",
    "sala_id",
    "fecha_hora",
    "precio",
}
PATRON_FECHA_HORA = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _error(codigo, descripcion):
    raise ApiError(400, codigo, "Solicitud inválida", descripcion)


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        _error("CAMPO_INVALIDO", f"{campo} debe ser un número entero positivo.")
    return valor


def _precio(valor):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        _error(
            "PRECIO_INVALIDO",
            "precio debe ser un número entero mayor o igual que cero.",
        )
    return valor


def _fecha_hora(valor, campo="fecha_hora"):
    if not isinstance(valor, str) or not valor.strip():
        _error(
            "FECHA_HORA_INVALIDA",
            f"{campo} debe tener formato de fecha y hora RFC 3339.",
        )

    texto = valor.strip()
    if PATRON_FECHA_HORA.fullmatch(texto) is None:
        _error(
            "FECHA_HORA_INVALIDA",
            f"{campo} debe tener formato de fecha y hora RFC 3339.",
        )

    if texto.endswith("Z"):
        texto = f"{texto[:-1]}+00:00"

    try:
        fecha = datetime.fromisoformat(texto)
    except ValueError:
        _error(
            "FECHA_HORA_INVALIDA",
            f"{campo} debe tener formato de fecha y hora RFC 3339.",
        )

    if fecha.tzinfo is None or fecha.utcoffset() is None:
        _error(
            "FECHA_HORA_INVALIDA",
            f"{campo} debe incluir el huso horario, por ejemplo -03:00.",
        )

    return fecha


def _estado(valor):
    if not isinstance(valor, str) or valor not in ESTADOS_FUNCION:
        _error(
            "ESTADO_INVALIDO",
            "estado debe ser 'programada' o 'cancelada'.",
        )
    return valor


def _validar_cuerpo(datos, requeridos, requiere_al_menos_un_campo=False):
    if not isinstance(datos, dict):
        _error(
            "CUERPO_INVALIDO",
            "El cuerpo de la solicitud debe ser un objeto JSON.",
        )

    desconocidos = set(datos) - CAMPOS_FUNCION
    if desconocidos:
        campos = ", ".join(sorted(desconocidos))
        _error("CAMPOS_DESCONOCIDOS", f"Campos no admitidos: {campos}.")

    faltantes = requeridos - set(datos)
    if faltantes:
        campos = ", ".join(sorted(faltantes))
        _error("CAMPOS_REQUERIDOS", f"Faltan campos requeridos: {campos}.")

    if requiere_al_menos_un_campo and not datos:
        _error("CUERPO_VACIO", "Debe indicar al menos un campo para modificar.")

    resultado = dict(datos)
    if "pelicula_id" in resultado:
        resultado["pelicula_id"] = _entero_positivo(
            resultado["pelicula_id"], "pelicula_id"
        )
    if "sala_id" in resultado:
        resultado["sala_id"] = _entero_positivo(resultado["sala_id"], "sala_id")
    if "fecha_hora" in resultado:
        resultado["fecha_hora"] = _fecha_hora(resultado["fecha_hora"])
    if "precio" in resultado:
        resultado["precio"] = _precio(resultado["precio"])
    if "estado" in resultado:
        resultado["estado"] = _estado(resultado["estado"])

    return resultado


def validar_creacion_funcion(datos):
    resultado = _validar_cuerpo(datos, CAMPOS_FUNCION_REQUERIDOS)
    resultado.setdefault("estado", "programada")
    return resultado


def validar_actualizacion_funcion(datos):
    return _validar_cuerpo(datos, set(), requiere_al_menos_un_campo=True)


def validar_filtros_funciones(args):
    pelicula_id = args.get("pelicula_id")
    desde = args.get("desde")
    hasta = args.get("hasta")
    estado = args.get("estado")

    if pelicula_id is not None:
        if not pelicula_id.isdecimal():
            _error(
                "FILTRO_INVALIDO",
                "pelicula_id debe ser un número entero positivo.",
            )
        pelicula_id = _entero_positivo(int(pelicula_id), "pelicula_id")

    desde = _fecha_hora(desde, "desde") if desde is not None else None
    hasta = _fecha_hora(hasta, "hasta") if hasta is not None else None
    estado = _estado(estado) if estado is not None else None

    if desde is not None and hasta is not None and desde > hasta:
        _error(
            "RANGO_FECHAS_INVALIDO",
            "desde debe ser anterior o igual que hasta.",
        )

    return {
        "pelicula_id": pelicula_id,
        "desde": desde,
        "hasta": hasta,
        "estado": estado,
    }


def validar_funcion_id(funcion_id):
    return _entero_positivo(funcion_id, "funcion_id")

