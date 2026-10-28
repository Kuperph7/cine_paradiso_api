from flask import jsonify


class ApiError(Exception):
    def __init__(self, status, code, message, description):
        super().__init__(description)
        self.status = status
        self.code = code
        self.message = message
        self.description = description


def error_response(error):
    return (
        jsonify(
            {
                "errors": [
                    {
                        "code": error.code,
                        "message": error.message,
                        "description": error.description,
                    }
                ]
            }
        ),
        error.status,
    )

