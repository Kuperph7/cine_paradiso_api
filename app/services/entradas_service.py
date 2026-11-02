"""Servicios de generación y validación de entradas."""
from flask import current_app
import jwt
from app.errors import ApiError
from app.repositories import entradas_repository


def _decodificar_token_cliente(token: str) -> dict:
    """Decodifica el token JWT y verifica que el usuario sea un cliente autenticado."""
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise ApiError(401, "TOKEN_EXPIRADO", "Sesión expirada", "El token ha expirado. Inicie sesión nuevamente.")
    except jwt.InvalidTokenError:
        raise ApiError(401, "TOKEN_INVALIDO", "Token inválido", "El token de autenticación no es válido.")

    if payload.get("rol") not in ("cliente", "administrador"):
        raise ApiError(403, "ACCESO_DENEGADO", "Sin permisos", "Se requiere ser un usuario autenticado.")

    return payload


def listar_mis_entradas(token: str) -> dict:
    """Retorna todas las entradas del cliente autenticado con función, butaca, estado y QR."""
    payload = _decodificar_token_cliente(token)
    usuario_id = payload["usuario_id"]
    entradas = entradas_repository.obtener_entradas_por_cliente(usuario_id)
    return {"entradas": entradas}


def consultar_entrada(token: str, entrada_id: int) -> dict:
    """Retorna el detalle de una entrada si pertenece al cliente autenticado."""
    payload = _decodificar_token_cliente(token)
    usuario_id = payload["usuario_id"]
    entrada = entradas_repository.obtener_entrada_por_id(entrada_id, usuario_id)
    if not entrada:
        raise ApiError(404, "ENTRADA_NO_ENCONTRADA", "Entrada no encontrada",
                       "La entrada no existe o no pertenece al usuario autenticado.")
    return entrada


def validar_entrada_qr(token_admin: str, codigo_qr: str, funcion_id: int) -> dict:
    """Verifica el QR contra la función solicitada y marca la entrada como utilizada de forma atómica."""
    from flask import current_app
    from app.services.admin_service import verificar_rol_administrador
    verificar_rol_administrador(token_admin)

    entrada = entradas_repository.obtener_entrada_por_qr(codigo_qr, funcion_id)

    if not entrada:
        raise ApiError(404, "ENTRADA_NO_ENCONTRADA", "QR inválido",
                       "El código QR no corresponde a ninguna entrada de esta función.")

    if entrada["estado"] == "cancelada":
        raise ApiError(409, "ENTRADA_CANCELADA", "Entrada cancelada",
                       "Esta entrada fue cancelada y no permite el ingreso.")

    if entrada["estado"] == "utilizada":
        raise ApiError(409, "ENTRADA_YA_UTILIZADA", "Entrada ya utilizada",
                       "Esta entrada ya fue registrada como utilizada en una validación anterior.")

    filas_afectadas = entradas_repository.marcar_entrada_utilizada(entrada["id"])

    if filas_afectadas == 0:
        raise ApiError(409, "CONFLICTO_VALIDACION", "Conflicto de validación",
                       "La entrada no pudo marcarse como utilizada. Es posible que ya haya sido validada simultáneamente.")

    return {
        "entrada_id": entrada["id"],
        "funcion_id": entrada["funcion_id"],
        "estado": "utilizada",
        "mensaje": "Ingreso permitido"
    }
