"""Servicios de autenticación y perfiles."""
from mysql.connector import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from app.errors import es_respuesta_error, respuesta_error
from app.repositories import usuarios_repository
from app.security import (
    ROL_CLIENTE,
    decodificar_token_recuperacion,
    generar_token_acceso,
    generar_token_recuperacion,
)

from app.integrations.email import (
    enviar_correo_recuperacion_password,
    enviar_correo_registro,
)

def _error_email_duplicado():
    return respuesta_error(
        409,
        "CONFLICTO_EMAIL",
        "Email ya registrado",
        "Ya existe una cuenta con este correo electrónico.",
    )


def registrar_cliente(data: dict) -> dict:
    """Registra un nuevo cliente con contraseña hasheada."""
    email = data["email"].strip().lower()
    nombre = data["nombre"].strip()
    password = data["password"]

    usuario_existente = usuarios_repository.obtener_usuario_por_email(email)
    if usuario_existente:
        return _error_email_duplicado()

    password_hash = generate_password_hash(password)

    try:
        nuevo_id = usuarios_repository.crear_usuario(
            nombre=nombre,
            email=email,
            password_hash=password_hash,
            rol=ROL_CLIENTE,
        )


    except IntegrityError:
        # La restricción UNIQUE es la defensa final si dos registros con el
        # mismo email superan la consulta previa al mismo tiempo.
        return _error_email_duplicado()

    try:
        enviar_correo_registro(email, nombre)
    except Exception as error:
        print(f"No se pudo enviar el correo de registro: {error}")

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
        return respuesta_error(
            401,
            "CREDENCIALES_INVALIDAS",
            "Error de autenticación",
            "Email o contraseña incorrectos.",
        )

    token = generar_token_acceso(usuario)
    if es_respuesta_error(token):
        return token

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
        return respuesta_error(
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


def solicitar_recuperacion_password(data: dict) -> dict:
    """Genera un token temporal y envía el correo de recuperación si el email existe."""
    email = data["email"].strip().lower()
    usuario = usuarios_repository.obtener_usuario_por_email(email)

    if not usuario:
        return respuesta_error(
            404,
            "USUARIO_NO_ENCONTRADO",
            "Correo no registrado",
            "No existe una cuenta registrada con ese correo electrónico.",
        )

    token = generar_token_recuperacion(usuario)
    if es_respuesta_error(token):
        return token

    try:
        enviar_correo_recuperacion_password(
            usuario["email"],
            usuario["nombre"],
            token,
        )
    except Exception as error:
        print(f"No se pudo enviar el correo de recuperación: {error}")

    return {
        "mensaje": "Se envió un correo con las instrucciones para restablecer tu contraseña.",
    }


def restablecer_password(data: dict) -> dict:
    """Valida el token de recuperación y actualiza la contraseña del usuario."""
    token = data["token"].strip()
    nueva_password = data["password"]

    identidad = decodificar_token_recuperacion(token)
    if es_respuesta_error(identidad):
        return identidad

    usuario = usuarios_repository.obtener_usuario_por_id(int(identidad["usuario_id"]))
    if not usuario:
        return respuesta_error(
            404,
            "USUARIO_NO_ENCONTRADO",
            "Usuario no encontrado",
            "El usuario asociado al código de recuperación no existe.",
        )

    password_hash = generate_password_hash(nueva_password)
    usuarios_repository.actualizar_password_usuario(
        int(usuario["id"]),
        password_hash,
    )

    return {
        "mensaje": "Tu contraseña ha sido actualizada correctamente. Ya podés iniciar sesión.",
    }
