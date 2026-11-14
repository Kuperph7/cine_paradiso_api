from flask import Blueprint, request, jsonify
from app.errors import es_respuesta_error
from app.validators.auth_validators import (
    validar_registro_usuario,
    validar_login_usuario,
)
from app.security import requerir_usuario_autenticado
from app.services.auth_service import (
    registrar_cliente,
    iniciar_sesion,
    obtener_perfil_usuario,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")



@auth_bp.route("/register", methods=["POST"])
def register():
    """Registra un nuevo usuario cliente en el sistema."""
    data = request.get_json()
    error = validar_registro_usuario(data)
    if es_respuesta_error(error):
        return error
    resultado = registrar_cliente(data)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Valida credenciales y genera la sesión con token de acceso JWT."""
    data = request.get_json()
    error = validar_login_usuario(data)
    if es_respuesta_error(error):
        return error
    resultado = iniciar_sesion(data)
    if es_respuesta_error(resultado):
        return resultado
    return jsonify(resultado), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Cierra la sesión indicando al cliente que debe eliminar el token."""
    return "", 204


@auth_bp.route("/perfil", methods=["GET"])
def perfil():
    """Obtiene el perfil del usuario autenticado a partir del token JWT."""
    identidad = requerir_usuario_autenticado()
    if es_respuesta_error(identidad):
        return identidad
    usuario = obtener_perfil_usuario(identidad["usuario_id"])
    if es_respuesta_error(usuario):
        return usuario
    return jsonify(usuario), 200
