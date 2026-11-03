"""Servicios de autenticación y perfiles."""
from datetime import datetime, timedelta, timezone
from flask import current_app
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from app.errors import ApiError
from app.repositories import usuarios_repository


def registrar_cliente(data: dict) -> dict:
    """Registra un nuevo cliente con contraseña hasheada."""
    email = data["email"].strip().lower()
    nombre = data["nombre"].strip()
    password = data["password"]

    usuario_existente = usuarios_repository.obtener_usuario_por_email(email)
    if usuario_existente:
        raise ApiError(
            status=409,
            code="CONFLICTO_EMAIL",
            message="Email ya registrado",
            description="Ya existe una cuenta con este correo electrónico."
        )

    password_hash = generate_password_hash(password)

    nuevo_id = usuarios_repository.crear_usuario(
        nombre=nombre,
        email=email,
        password_hash=password_hash,
        rol="cliente"
    )

    return {
        "id": nuevo_id,
        "mensaje": "Usuario registrado exitosamente"
    }


def iniciar_sesion(data: dict) -> dict:
    """Valida credenciales y genera el token de acceso JWT."""
    email = data["email"].strip().lower()
    password = data["password"]

    usuario = usuarios_repository.obtener_usuario_por_email(email)

    if not usuario or not check_password_hash(usuario["password_hash"], password):
        raise ApiError(401, "CREDENCIALES_INVALIDAS", "Error de autenticación", "Email o contraseña incorrectos.")

    payload = {
        "usuario_id": usuario["id"],
        "email": usuario["email"],
        "rol": usuario["rol"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=4)
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": usuario["rol"]
        }
    }


def obtener_perfil_usuario(token: str) -> dict:
    """Decodifica el token JWT y obtiene los datos del perfil del usuario."""
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRADO", "Sesión expirada", "El token ha expirado. Inicie sesión nuevamente.")
    except jwt.InvalidTokenError:
        raise ApiError(401, "TOKEN_INVALIDO", "Token inválido", "El token de autenticación no es válido.")

    usuario = usuarios_repository.obtener_usuario_por_id(payload["usuario_id"])
    if not usuario:
        raise ApiError(404, "USUARIO_NO_ENCONTRADO", "Usuario no encontrado", "El usuario asociado al token no existe.")

    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "rol": usuario["rol"]
    }
