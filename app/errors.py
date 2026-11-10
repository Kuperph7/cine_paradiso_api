from flask import jsonify


def crear_error(status, code, message, description):
    return {
        "status": status,
        "code": code,
        "message": message,
        "description": description
    }

def error_response(error):
    """
    Genera una respuesta JSON a partir de un diccionario de error.
    """
    return (
        jsonify(
            {
                "codigo": error["code"],
                "mensaje": error["message"],
                "detalles": [
                    {
                        "campo": "general",
                        "mensaje": error["description"],
                    }
                ],
            }
        ),
        error["status"],
    )