"""Servicios de autenticación y perfiles."""

from werkzeug.security import generate_password_hash
from app.errors import ApiError
from app.repositories import usuarios_repository


def registrar_cliente(data: dict) -> dict:
    """Registra un nuevo cliente con contraseña hasheada."""
    email = data["email"].strip().lower()
    nombre = data["nombre"].strip()
    password = data["password"]

    # 1. Verificar si el email ya existe en la base de datos
    usuario_existente = usuarios_repository.obtener_usuario_por_email(email)
    if usuario_existente:
        raise ApiError(
            status=409,
            code="CONFLICTO_EMAIL",
            message="Email ya registrado",
            description="Ya existe una cuenta con este correo electrónico."
        )

    # 2. Hashear la contraseña (¡Seguridad fundamental!)
    password_hash = generate_password_hash(password)

    # 3. Guardar en la base de datos con rol 'cliente'
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
