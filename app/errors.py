"""Contrato y manejadores centralizados para los errores de la API."""

from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException


class ApiError(Exception):
    def __init__(self, status, code, message, description):
        super().__init__(description)
        self.status = status
        self.code = code
        self.message = message
        self.description = description


def error_response(error):
    """Convierte un error de negocio al contrato JSON público de la API."""
    return (
        jsonify(
            {
                "codigo": error.code,
                "mensaje": error.message,
                "detalles": [
                    {
                        "campo": "general",
                        "mensaje": error.description,
                    }
                ],
            }
        ),
        error.status,
    )


HTTP_ERROR_DEFINITIONS = {
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
}


def http_error_response(error):
    """Normaliza los errores HTTP generados por Flask/Werkzeug."""
    status = error.code or 500
    code, message, description = HTTP_ERROR_DEFINITIONS.get(
        status,
        (
            f"ERROR_HTTP_{status}",
            "No fue posible procesar la solicitud",
            "Ocurrió un error al procesar la solicitud.",
        ),
    )
    return error_response(ApiError(status, code, message, description))


def unexpected_error_response(error):
    """Evita respuestas HTML y la exposición de detalles ante fallos internos."""
    current_app.logger.error(
        "Error no controlado al procesar la solicitud",
        exc_info=(type(error), error, error.__traceback__),
    )
    return error_response(
        ApiError(
            500,
            "ERROR_INTERNO",
            "Error interno del servidor",
            "No fue posible procesar la solicitud.",
        )
    )


def register_error_handlers(app):
    """Registra en una aplicación Flask todos los manejadores de la API."""
    app.register_error_handler(ApiError, error_response)
    app.register_error_handler(HTTPException, http_error_response)
    app.register_error_handler(Exception, unexpected_error_response)

