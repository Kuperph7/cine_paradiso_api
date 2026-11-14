"""Validaciones del contrato de servicios adicionales."""

from app.errors import respuesta_error


CAMPOS_CREACION = {"nombre", "descripcion", "precio"}
CAMPOS_ACTUALIZACION = {"nombre", "descripcion", "precio", "activo"}


def _error(codigo, descripcion):
    return respuesta_error(400, codigo, "Solicitud inválida", descripcion)


def _entero_positivo(valor, campo):
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        return _error("CAMPO_INVALIDO", f"{campo} debe ser un entero positivo.")
    return valor


def _validar_cuerpo(datos, campos_admitidos, requeridos):
    if not isinstance(datos, dict):
        return _error(
            "CUERPO_INVALIDO",
            "El cuerpo de la solicitud debe ser un objeto JSON.",
        )

    desconocidos = set(datos) - campos_admitidos
    if desconocidos:
        nombres = ", ".join(sorted(desconocidos))
        return _error("CAMPOS_DESCONOCIDOS", f"Campos no admitidos: {nombres}.")

    faltantes = requeridos - set(datos)
    if faltantes:
        nombres = ", ".join(sorted(faltantes))
        return _error("CAMPOS_REQUERIDOS", f"Faltan campos requeridos: {nombres}.")

    if not datos:
        return _error("CUERPO_VACIO", "Debe indicar al menos un campo.")

    resultado = dict(datos)
    if "nombre" in resultado:
        nombre = resultado["nombre"]
        if not isinstance(nombre, str) or not nombre.strip():
            return _error("CAMPO_INVALIDO", "nombre debe ser un texto no vacío.")
        resultado["nombre"] = nombre.strip()

    if "descripcion" in resultado:
        descripcion = resultado["descripcion"]
        if not isinstance(descripcion, str) or not descripcion.strip():
            return _error(
                "CAMPO_INVALIDO",
                "descripcion debe ser un texto no vacío.",
            )
        resultado["descripcion"] = descripcion.strip()

    if "precio" in resultado:
        precio = resultado["precio"]
        if isinstance(precio, bool) or not isinstance(precio, int) or precio < 0:
            return _error(
                "CAMPO_INVALIDO",
                "precio debe ser un entero mayor o igual a cero.",
            )

    if "activo" in resultado and not isinstance(resultado["activo"], bool):
        return _error("CAMPO_INVALIDO", "activo debe ser booleano.")

    return resultado


def validar_creacion_servicio(datos):
    return _validar_cuerpo(datos, CAMPOS_CREACION, {"nombre", "precio"})


def validar_actualizacion_servicio(datos):
    return _validar_cuerpo(datos, CAMPOS_ACTUALIZACION, set())


def validar_servicio_id(servicio_id):
    return _entero_positivo(servicio_id, "servicio_id")


def validar_filtro_incluir_inactivos(args):
    valor = args.get("incluir_inactivos")
    if valor is None:
        return False
    if valor == "true":
        return True
    if valor == "false":
        return False
    return _error(
        "FILTRO_INVALIDO",
        "incluir_inactivos solo admite true o false.",
    )
