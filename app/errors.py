"""Funciones para construir respuestas de error uniformes de la API."""


ERRORES_HTTP = {
    400: (
        "DATOS_INVALIDOS",
        "Los datos enviados son inválidos",
        "Revise el formato y los datos de la solicitud.",
    ),
    401: (
        "AUTENTICACION_REQUERIDA",
        "Autenticación requerida",
        "Debe iniciar sesión para realizar esta operación.",
    ),
    403: (
        "PERMISO_DENEGADO",
        "Permiso denegado",
        "No tiene permisos para realizar esta operación.",
    ),
    404: (
        "RECURSO_NO_ENCONTRADO",
        "Recurso no encontrado",
        "El recurso solicitado no existe.",
    ),
    405: (
        "METODO_NO_PERMITIDO",
        "Método no permitido",
        "El recurso no admite el método HTTP utilizado.",
    ),
    409: (
        "CONFLICTO",
        "Conflicto con el recurso",
        "La operación entra en conflicto con el estado actual del recurso.",
    ),
    415: (
        "TIPO_CONTENIDO_NO_SOPORTADO",
        "Tipo de contenido no soportado",
        "Envíe el cuerpo de la solicitud como application/json.",
    ),
    422: (
        "DATOS_INVALIDOS",
        "Los datos enviados son inválidos",
        "La solicitud contiene datos que no pueden procesarse.",
    ),
    500: (
        "ERROR_INTERNO",
        "Error interno del servidor",
        "No fue posible procesar la solicitud.",
    ),
}


def respuesta_error(codigo_http, codigo, mensaje, detalle, campo="general"):
    """Devuelve el único contrato usado por todos los errores de la API."""
    return (
        {
            "codigo": codigo,
            "mensaje": mensaje,
            "detalles": [
                {
                    "campo": campo,
                    "mensaje": detalle,
                }
            ],
        },
        codigo_http,
    )


def es_respuesta_error(resultado):
    """Indica si un resultado es una respuesta de error creada por este módulo."""
    return (
        isinstance(resultado, tuple)
        and len(resultado) == 2
        and isinstance(resultado[0], dict)
        and isinstance(resultado[1], int)
        and resultado[1] >= 400
        and set(resultado[0]) == {"codigo", "mensaje", "detalles"}
    )


def respuesta_error_http(codigo_http):
    """Crea la respuesta uniforme correspondiente a un código HTTP."""
    codigo, mensaje, detalle = ERRORES_HTTP.get(
        codigo_http,
        (
            f"ERROR_HTTP_{codigo_http}",
            "No fue posible procesar la solicitud",
            "Ocurrió un error al procesar la solicitud.",
        ),
    )
    return respuesta_error(codigo_http, codigo, mensaje, detalle)


def registrar_manejadores_errores(app):
    """Registra por código los errores que Flask puede generar automáticamente."""
    for codigo_http in ERRORES_HTTP:
        app.register_error_handler(
            codigo_http,
            lambda _error, codigo=codigo_http: respuesta_error_http(codigo),
        )

