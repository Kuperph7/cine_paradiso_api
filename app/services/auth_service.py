"""Servicios de autenticación y perfiles."""
from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import ApiError
from app.repositories import usuarios_repository
from app.security import ROL_CLIENTE, generar_token_acceso


def _error_email_duplicado():
    return ApiError(
        status=409,
        code="CONFLICTO_EMAIL",
        message="Email ya registrado",
        description="Ya existe una cuenta con este correo electrónico.",
    )


def registrar_cliente(data: dict) -> dict:
    """Registra un nuevo cliente con contraseña hasheada."""
    email = data["email"].strip().lower()
    nombre = data["nombre"].strip()
    password = data["password"]

    usuario_existente = usuarios_repository.obtener_usuario_por_email(email)
    if usuario_existente:
        raise _error_email_duplicado()

    password_hash = generate_password_hash(password)

    try:
        nuevo_id = usuarios_repository.crear_usuario(
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            rol=ROL_CLIENTE,
        )
    except IntegrityError as error:
        # La restricción UNIQUE es la defensa final si dos registros con el
        # mismo email superan la consulta previa al mismo tiempo.
        raise _error_email_duplicado() from error

    return {
        "id": nuevo_id,
        "mensaje": "Usuario registrado exitosamente",
    }


def iniciar_sesion(data: dict) -> dict:
    """Valida credenciales y genera el token de acceso JWT."""
    email = data["email"].strip().lower()
    password = data["password"]

    usuario = usuarios_repository.obtener_usuario_por_email(email)

    if not usuario or not check_password_hash(usuario["password_hash"], password):
        raise ApiError(
            401,
            "CREDENCIALES_INVALIDAS",
            "Error de autenticación",
            "Email o contraseña incorrectos.",
        )

    token = generar_token_acceso(usuario)

    return {
        "token": token,
        "usuario": {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": usuario["rol"],
        },
    }


def obtener_perfil_usuario(usuario_id: int) -> dict:
    """Obtiene el perfil de una identidad previamente autenticada."""
    usuario = usuarios_repository.obtener_usuario_por_id(usuario_id)
    if not usuario:
        raise ApiError(
            404,
            "USUARIO_NO_ENCONTRADO",
            "Usuario no encontrado",
            "El usuario asociado al token no existe.",
        )

    return {
        "id": usuario["id"],
        "nombre": usuario["nombre"],
        "email": usuario["email"],
        "rol": usuario["rol"],
    }
