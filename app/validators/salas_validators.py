"""Validaciones de la gestión administrativa de salas."""

from app.errors import es_respuesta_error, respuesta_error


CAMPOS_CREACION = {"local_id", "nombre", "filas", "butacas_por_fila"}
CAMPOS_ACTUALIZACION = {"nombre", "filas", "butacas_por_fila", "activa"}
MAXIMO_FILAS = 18278


def _error(codigo, descripcion):
    return respuesta_error(400, codigo, "Solicitud inválida", descripcion)


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        return _error("CAMPO_INVALIDO", f"{campo} debe ser un número entero positivo.")
    return valor


def _validar_cuerpo(datos, campos_admitidos, requeridos):
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
    if "local_id" in resultado:
        valor = _entero_positivo(
            resultado["local_id"], "local_id"
        )
        if es_respuesta_error(valor):
            return valor
        resultado["local_id"] = valor
    if "nombre" in resultado:
        if not isinstance(resultado["nombre"], str) or not resultado["nombre"].strip():
            return _error("CAMPO_INVALIDO", "nombre debe ser un texto no vacío.")
        resultado["nombre"] = resultado["nombre"].strip()
    if "filas" in resultado:
        valor = _entero_positivo(resultado["filas"], "filas")
        if es_respuesta_error(valor):
            return valor
        resultado["filas"] = valor
        if resultado["filas"] > MAXIMO_FILAS:
            return _error(
                "DISTRIBUCION_INVALIDA",
                f"filas no puede superar {MAXIMO_FILAS}.",
            )
    if "butacas_por_fila" in resultado:
        valor = _entero_positivo(
            resultado["butacas_por_fila"], "butacas_por_fila"
        )
        if es_respuesta_error(valor):
            return valor
        resultado["butacas_por_fila"] = valor
    if "activa" in resultado and not isinstance(resultado["activa"], bool):
        return _error("CAMPO_INVALIDO", "activa debe ser un valor booleano.")

    return resultado


def validar_creacion_sala(datos):
    return _validar_cuerpo(datos, CAMPOS_CREACION, CAMPOS_CREACION)


def validar_actualizacion_sala(datos):
    return _validar_cuerpo(datos, CAMPOS_ACTUALIZACION, set())


def validar_filtros_salas(args):
    incluir_inactivas = args.get("incluir_inactivas")
    if incluir_inactivas is None:
        return False
    if incluir_inactivas.lower() == "true":
        return True
    if incluir_inactivas.lower() == "false":
        return False
    return _error("FILTRO_INVALIDO", "incluir_inactivas debe ser true o false.")


def validar_sala_id(sala_id):
    return _entero_positivo(sala_id, "sala_id")
