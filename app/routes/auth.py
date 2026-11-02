from flask import Blueprint, request, jsonify
from app.validators.auth_validators import validar_registro_usuario
from app.services.auth_service import registrar_cliente

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



@auth_bp.route("/register", methods=["POST"])
def register():
    """Registra un nuevo usuario cliente en el sistema."""
    data = request.get_json()

    # 1. Validar los datos de entrada
    validar_registro_usuario(data)

    # 2. Ejecutar la lógica de negocio en el servicio
    resultado = registrar_cliente(data)

    # 3. Responder con código 201 Created y el JSON acordado en Swagger
    return jsonify(resultado), 201