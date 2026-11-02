from flask import Blueprint, request, jsonify
from app.validators.auth_validators import validar_registro_usuario, validar_login_usuario
from app.services.auth_service import registrar_cliente, iniciar_sesion

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



@auth_bp.route("/register", methods=["POST"])
def register():
    """Registra un nuevo usuario cliente en el sistema."""
    data = request.get_json()
    validar_registro_usuario(data)
    resultado = registrar_cliente(data)
    return jsonify(resultado), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Valida credenciales y genera la sesión con token de acceso JWT."""
    data = request.get_json()
    validar_login_usuario(data)
    resultado = iniciar_sesion(data)
    return jsonify(resultado), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión indicando al cliente que debe eliminar el token."""
    return "", 204