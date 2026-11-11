"""Validaciones de las operaciones administrativas."""
from app.errors import es_respuesta_error, respuesta_error
from urllib.parse import urlparse
from datetime import datetime
from zoneinfo import ZoneInfo
from app.validators.common import (
    validation_error,
    validate_choice,
    validate_date_range,
    validate_non_negative_number,
    validate_positive_integer,
)

ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")
FUNCTION_STATES = frozenset({"programada", "cancelada"})
DEFAULT_FUNCTION_STATE = "programada"

def validar_creacion_servicio(data: dict):
    """Valida los campos obligatorios y tipos para crear un servicio."""
    if not data or not isinstance(data, dict):
        return validation_error("El cuerpo de la solicitud debe ser un JSON válido.")

    nombre = data.get("nombre")
    if not nombre or not isinstance(nombre, str) or not nombre.strip():
        return validation_error("El campo 'nombre' es obligatorio y no puede estar vacío.")

    precio = data.get("precio")
    if isinstance(precio, bool) or not isinstance(precio, int) or precio < 0:
        return validation_error("El campo 'precio' debe ser un número entero mayor o igual a 0.")

    descripcion = data.get("descripcion")
    if descripcion is not None and not isinstance(descripcion, str):
        return validation_error("El campo 'descripcion' debe ser una cadena de texto.")


def validar_actualizacion_servicio(data: dict):
    """Valida los campos a modificar de un servicio existente."""
    if not data or not isinstance(data, dict):
        return validation_error("El cuerpo de la solicitud debe ser un JSON válido.")

    campos_validos = {"nombre", "descripcion", "precio"}
    if not any(campo in data for campo in campos_validos):
        return validation_error("Debe proporcionar al menos un campo válido para actualizar.")

    if "nombre" in data:
        nombre = data["nombre"]
        if not isinstance(nombre, str) or not nombre.strip():
            return validation_error("El campo 'nombre' no puede estar vacío.")

    if "precio" in data:
        precio = data["precio"]
        if isinstance(precio, bool) or not isinstance(precio, int) or precio < 0:
            return validation_error("El campo 'precio' debe ser un número entero mayor o igual a 0.")

    if "descripcion" in data:
        descripcion = data["descripcion"]
        if not isinstance(descripcion, str):
            return validation_error("El campo 'descripcion' debe ser una cadena de texto.")


def validar_entrada_qr_request(data: dict):
    """Valida que el cuerpo del request incluya codigo_qr y funcion_id."""
    if not data or not isinstance(data, dict):
        return validation_error("El cuerpo de la solicitud debe ser un JSON válido.")

    codigo_qr = data.get("codigo_qr")
    if not codigo_qr or not isinstance(codigo_qr, str) or not codigo_qr.strip():
        return validation_error("El campo 'codigo_qr' es obligatorio.")

    funcion_id = data.get("funcion_id")
    if (
        isinstance(funcion_id, bool)
        or not isinstance(funcion_id, int)
        or funcion_id < 1
    ):
        return validation_error("El campo 'funcion_id' debe ser un entero positivo.")


CAMPOS_PELICULA_CREACION = {
    "id_externo",
    "titulo",
    "sinopsis",
    "poster_url",
    "duracion_minutos",
    "clasificacion",
    "genero",
}
CAMPOS_PELICULA_ACTUALIZACION = {
    "titulo",
    "sinopsis",
    "poster_url",
    "duracion_minutos",
    "clasificacion",
    "genero",
    "activa",
}
CAMPOS_PELICULA_REQUERIDOS = {
    "titulo",
    "sinopsis",
    "poster_url",
    "duracion_minutos",
    "clasificacion",
    "genero",
}


def _error(codigo, descripcion):
    return respuesta_error(400, codigo, "Solicitud inválida", descripcion)


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        return _error("CAMPO_INVALIDO", f"{campo} debe ser un número entero positivo.")
    return valor


def _texto_no_vacio(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        return _error("CAMPO_INVALIDO", f"{campo} debe ser un texto no vacío.")
    return valor.strip()


def _url(valor, campo):
    texto = _texto_no_vacio(valor, campo)
    if es_respuesta_error(texto):
        return texto
    url = urlparse(texto)
    if url.scheme not in {"http", "https"} or not url.netloc:
        return _error("URL_INVALIDA", f"{campo} debe ser una URL HTTP o HTTPS válida.")
    return texto


def _validar_cuerpo_pelicula(datos, campos_admitidos, requeridos):
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

    if not datos:
        return _error("CUERPO_VACIO", "Debe indicar al menos un campo para modificar.")

    resultado = dict(datos)
    if "id_externo" in resultado:
        id_externo = resultado["id_externo"]
        if isinstance(id_externo, bool) or not isinstance(id_externo, int):
            return _error("CAMPO_INVALIDO", "id_externo debe ser un número entero.")

    for campo in ("titulo", "sinopsis", "clasificacion", "genero"):
        if campo in resultado:
            valor = _texto_no_vacio(resultado[campo], campo)
            if es_respuesta_error(valor):
                return valor
            resultado[campo] = valor

    if "poster_url" in resultado:
        poster_url = _url(resultado["poster_url"], "poster_url")
        if es_respuesta_error(poster_url):
            return poster_url
        resultado["poster_url"] = poster_url
    if "duracion_minutos" in resultado:
        duracion = _entero_positivo(
            resultado["duracion_minutos"], "duracion_minutos"
        )
        if es_respuesta_error(duracion):
            return duracion
        resultado["duracion_minutos"] = duracion
    if "activa" in resultado and not isinstance(resultado["activa"], bool):
        return _error("CAMPO_INVALIDO", "activa debe ser un valor booleano.")

    return resultado


def validar_creacion_pelicula(datos):
    return _validar_cuerpo_pelicula(
        datos,
        CAMPOS_PELICULA_CREACION,
        CAMPOS_PELICULA_REQUERIDOS,
    )


def validar_actualizacion_pelicula(datos):
    return _validar_cuerpo_pelicula(
        datos,
        CAMPOS_PELICULA_ACTUALIZACION,
        set(),
    )


def validar_filtros_peliculas(args):
    titulo = args.get("titulo")
    incluir_inactivas = args.get("incluir_inactivas")

    if titulo is not None:
        titulo = titulo.strip() or None

    if incluir_inactivas is None:
        incluir_inactivas = False
    elif incluir_inactivas.lower() == "true":
        incluir_inactivas = True
    elif incluir_inactivas.lower() == "false":
        incluir_inactivas = False
    else:
        return _error(
            "FILTRO_INVALIDO",
            "incluir_inactivas debe ser true o false.",
        )

    return {
        "titulo": titulo,
        "incluir_inactivas": incluir_inactivas,
    }


def validar_busqueda_peliculas_externas(args):
    titulo = args.get("titulo")
    if titulo is None:
        return _error("CAMPO_REQUERIDO", "El parámetro titulo es obligatorio.")
    return _texto_no_vacio(titulo, "titulo")


def validar_pelicula_id(pelicula_id):
    return _entero_positivo(pelicula_id, "pelicula_id")

def _validar_fecha(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        return _error("FILTRO_INVALIDO", f"{campo} debe ser una fecha válida.")

    try:
        fecha = datetime.fromisoformat(valor)

        if fecha.tzinfo is None:
            return _error(
                "FILTRO_INVALIDO",
                f"{campo} debe tener formato ISO 8601 con zona horaria.",
            )

        return fecha.astimezone(ZONA_HORARIA).replace(tzinfo=None)

    except ValueError:
        return _error(
            "FILTRO_INVALIDO",
            f"{campo} debe tener formato ISO 8601 con zona horaria.",
        )


def validar_filtros_estadisticas(args):
    desde = args.get("desde")
    hasta = args.get("hasta")

    if (desde is None) != (hasta is None):
        return _error(
            "FILTROS_INCOMPLETOS",
            "Los parámetros desde y hasta deben enviarse juntos.",
        )

    if desde is None:
        return {
            "desde": None,
            "hasta": None,
        }

    fecha_desde = _validar_fecha(desde, "desde")
    if es_respuesta_error(fecha_desde):
        return fecha_desde
    fecha_hasta = _validar_fecha(hasta, "hasta")
    if es_respuesta_error(fecha_hasta):
        return fecha_hasta

    if fecha_desde > fecha_hasta:
        return _error(
            "RANGO_FECHAS_INVALIDO",
            "La fecha desde no puede ser posterior a hasta.",
        )

    return {
        "desde": fecha_desde,
        "hasta": fecha_hasta,
    }
def validate_function_state(value):
    return validate_choice(value, "estado", FUNCTION_STATES)


def validate_function_price(value):
    return validate_non_negative_number(value, "precio")


def validate_service_price(value):
    return validate_non_negative_number(value, "precio")


def validate_room_dimensions(rows, seats_per_row):
    filas = validate_positive_integer(rows, "filas")
    if es_respuesta_error(filas):
        return filas
    butacas = validate_positive_integer(seats_per_row, "butacas_por_fila")
    if es_respuesta_error(butacas):
        return butacas
    return filas, butacas


def validate_movie_duration(value):
    return validate_positive_integer(value, "duracion_minutos")


def validate_movie_availability(start, end):
    return validate_date_range(
        start,
        end,
        "disponible_desde",
        "disponible_hasta",
    )
