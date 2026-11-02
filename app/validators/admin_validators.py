"""Validaciones de las operaciones administrativas."""

from urllib.parse import urlparse

from app.errors import ApiError


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
    raise ApiError(400, codigo, "Solicitud inválida", descripcion)


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        _error("CAMPO_INVALIDO", f"{campo} debe ser un número entero positivo.")
    return valor


def _texto_no_vacio(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        _error("CAMPO_INVALIDO", f"{campo} debe ser un texto no vacío.")
    return valor.strip()


def _url(valor, campo):
    texto = _texto_no_vacio(valor, campo)
    url = urlparse(texto)
    if url.scheme not in {"http", "https"} or not url.netloc:
        _error("URL_INVALIDA", f"{campo} debe ser una URL HTTP o HTTPS válida.")
    return texto


def _validar_cuerpo_pelicula(datos, campos_admitidos, requeridos):
    if not isinstance(datos, dict):
        _error(
            "CUERPO_INVALIDO",
            "El cuerpo de la solicitud debe ser un objeto JSON.",
        )

    desconocidos = set(datos) - campos_admitidos
    if desconocidos:
        campos = ", ".join(sorted(desconocidos))
        _error("CAMPOS_DESCONOCIDOS", f"Campos no admitidos: {campos}.")

    faltantes = requeridos - set(datos)
    if faltantes:
        campos = ", ".join(sorted(faltantes))
        _error("CAMPOS_REQUERIDOS", f"Faltan campos requeridos: {campos}.")

    if not datos:
        _error("CUERPO_VACIO", "Debe indicar al menos un campo para modificar.")

    resultado = dict(datos)
    if "id_externo" in resultado:
        id_externo = resultado["id_externo"]
        if isinstance(id_externo, bool) or not isinstance(id_externo, int):
            _error("CAMPO_INVALIDO", "id_externo debe ser un número entero.")

    for campo in ("titulo", "sinopsis", "clasificacion", "genero"):
        if campo in resultado:
            resultado[campo] = _texto_no_vacio(resultado[campo], campo)

    if "poster_url" in resultado:
        resultado["poster_url"] = _url(resultado["poster_url"], "poster_url")
    if "duracion_minutos" in resultado:
        resultado["duracion_minutos"] = _entero_positivo(
            resultado["duracion_minutos"], "duracion_minutos"
        )
    if "activa" in resultado and not isinstance(resultado["activa"], bool):
        _error("CAMPO_INVALIDO", "activa debe ser un valor booleano.")

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
        _error(
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
        _error("CAMPO_REQUERIDO", "El parámetro titulo es obligatorio.")
    return _texto_no_vacio(titulo, "titulo")


def validar_pelicula_id(pelicula_id):
    return _entero_positivo(pelicula_id, "pelicula_id")

