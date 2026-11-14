"""Servicios de generación y validación de entradas."""
from app.errors import respuesta_error
from app.repositories import entradas_repository


def listar_mis_entradas(usuario_id: int) -> dict:
    """Retorna todas las entradas del cliente autenticado con función, butaca, estado y QR."""
    entradas = entradas_repository.obtener_entradas_por_cliente(usuario_id)
    return {"entradas": entradas}


def consultar_entrada(usuario_id: int, entrada_id: int) -> dict:
    """Retorna el detalle de una entrada si pertenece al cliente autenticado."""
    entrada = entradas_repository.obtener_entrada_por_id(entrada_id, usuario_id)
    if not entrada:
        return respuesta_error(
            404,
            "ENTRADA_NO_ENCONTRADA",
            "Entrada no encontrada",
            "La entrada no existe o no pertenece al usuario autenticado.",
        )
    return entrada


def validar_entrada_qr(codigo_qr: str, funcion_id: int) -> dict:
    """Verifica el QR contra la función solicitada y marca la entrada como utilizada de forma atómica."""
    entrada = entradas_repository.obtener_entrada_por_qr(codigo_qr, funcion_id)

    if not entrada:
        return respuesta_error(
            404,
            "ENTRADA_NO_ENCONTRADA",
            "QR inválido",
            "El código QR no corresponde a ninguna entrada de esta función.",
        )

    if entrada["estado"] == "cancelada":
        return respuesta_error(
            409,
            "ENTRADA_CANCELADA",
            "Entrada cancelada",
            "Esta entrada fue cancelada y no permite el ingreso.",
        )

    if entrada["estado"] == "utilizada":
        return respuesta_error(
            409,
            "ENTRADA_YA_UTILIZADA",
            "Entrada ya utilizada",
            "Esta entrada ya fue registrada como utilizada en una validación anterior.",
        )

    filas_afectadas = entradas_repository.marcar_entrada_utilizada(entrada["id"])

    if filas_afectadas == 0:
        return respuesta_error(
            409,
            "CONFLICTO_VALIDACION",
            "Conflicto de validación",
            "La entrada no pudo marcarse como utilizada. Es posible que ya "
            "haya sido validada simultáneamente.",
        )

    return {
        "entrada_id": entrada["id"],
        "funcion_id": entrada["funcion_id"],
        "estado": "utilizada",
        "mensaje": "Ingreso permitido"
    }
