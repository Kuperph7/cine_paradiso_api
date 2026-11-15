"""Reservas temporales y resolución de pagos simulados."""

import uuid
from datetime import timezone

from mysql.connector import IntegrityError

from app.db import get_db_connection
from app.errors import es_respuesta_error, respuesta_error
from app.integrations.qr import generar_token_qr
from app.repositories.compras_repository import (
    agregar_servicios_compra,
    bloquear_butacas,
    buscar_compra_por_id,
    buscar_ocupaciones_butacas,
    confirmar_compra as confirmar_compra_repository,
    crear_compra,
)
from app.repositories.entradas_repository import crear_entrada
from app.repositories.funciones_repository import buscar_funcion_para_compra
from app.repositories.reservas_repository import (
    buscar_reserva,
    buscar_reserva_activa_usuario,
    cancelar_reserva as cancelar_reserva_repository,
    confirmar_reserva,
    crear_reserva as insertar_reserva,
    iniciar_pago_reserva,
    liberar_butacas_reserva,
    listar_butacas_reserva,
    marcar_reservas_vencidas,
    rechazar_pago_reserva,
    retener_butacas,
    vender_butacas_reserva,
)
from app.services.compras_service import (
    _completar_compra,
    _preparar_servicios,
    _validar_funcion,
)


ESTADOS_CON_BLOQUEO = {"retenida", "pago_en_proceso", "reservada"}


def _fecha_utc_iso(fecha):
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    else:
        fecha = fecha.astimezone(timezone.utc)
    return fecha.isoformat().replace("+00:00", "Z")


def _serializar_reserva(conexion, reserva, butacas=None):
    if butacas is None:
        butacas = listar_butacas_reserva(conexion, reserva["id"])
    return {
        "id": reserva["id"],
        "usuario_id": int(reserva["usuario_id"]),
        "funcion_id": int(reserva["funcion_id"]),
        "estado": reserva["estado"],
        "creada_en": _fecha_utc_iso(reserva.get("creada_en")),
        "expira_en": _fecha_utc_iso(reserva.get("expira_en")),
        "compra_id": (
            int(reserva["compra_id"])
            if reserva.get("compra_id") is not None
            else None
        ),
        "butacas": [
            {
                "id": int(butaca["butaca_id"]),
                "fila": butaca["fila"],
                "numero": int(butaca["numero"]),
            }
            for butaca in butacas
        ],
    }


def _reserva_no_encontrada():
    return respuesta_error(
        404,
        "RESERVA_NO_ENCONTRADA",
        "Reserva no encontrada",
        "No existe una reserva con ese identificador.",
    )


def _reserva_ajena():
    return respuesta_error(
        403,
        "RESERVA_AJENA",
        "Permiso denegado",
        "La reserva no pertenece al usuario autenticado.",
    )


def _reserva_vencida():
    return respuesta_error(
        410,
        "RESERVA_VENCIDA",
        "La reserva venció",
        "Las butacas dejaron de estar retenidas. Seleccionalas nuevamente.",
    )


def _butaca_no_disponible():
    return respuesta_error(
        409,
        "BUTACA_NO_DISPONIBLE",
        "Butaca no disponible",
        "Una de las butacas fue retenida o vendida por otra operación.",
    )


def _bloqueo_vigente(ocupacion):
    if ocupacion["estado"] in {"vendida", "ocupada"}:
        return True
    return (
        ocupacion["estado"] in ESTADOS_CON_BLOQUEO
        and bool(ocupacion.get("vigente"))
    )


def _validar_butacas_de_sala(conexion, funcion, butaca_ids):
    butacas = bloquear_butacas(conexion, funcion["sala_id"], butaca_ids)
    encontradas = {int(butaca["id"]) for butaca in butacas}
    if encontradas != set(butaca_ids):
        return respuesta_error(
            404,
            "BUTACA_NO_ENCONTRADA",
            "Butaca no encontrada",
            "Una o más butacas no existen, están inactivas o son de otra sala.",
        )


def _buscar_reintento_propio(
    conexion,
    usuario_id,
    butaca_ids,
    ocupaciones_vigentes,
):
    if len(ocupaciones_vigentes) != len(butaca_ids):
        return None
    reserva_ids = {item.get("reserva_id") for item in ocupaciones_vigentes}
    if None in reserva_ids or len(reserva_ids) != 1:
        return None
    reserva = buscar_reserva(conexion, reserva_ids.pop(), bloquear=True)
    if (
        reserva is None
        or int(reserva["usuario_id"]) != usuario_id
        or reserva["estado"] != "retenida"
        or not reserva["vigente"]
    ):
        return None
    reservadas = {
        int(item["butaca_id"])
        for item in listar_butacas_reserva(conexion, reserva["id"])
    }
    return reserva if reservadas == set(butaca_ids) else None


def crear_reserva(usuario_id, funcion_id, butaca_ids):
    conexion = get_db_connection()
    try:
        conexion.start_transaction()
        funcion = buscar_funcion_para_compra(conexion, funcion_id)
        error = _validar_funcion(funcion)
        if es_respuesta_error(error):
            conexion.rollback()
            return error
        error = _validar_butacas_de_sala(conexion, funcion, butaca_ids)
        if es_respuesta_error(error):
            conexion.rollback()
            return error

        ocupaciones = buscar_ocupaciones_butacas(
            conexion,
            funcion_id,
            butaca_ids,
        )
        vigentes = [item for item in ocupaciones if _bloqueo_vigente(item)]
        reintento = _buscar_reintento_propio(
            conexion,
            usuario_id,
            butaca_ids,
            vigentes,
        )
        if reintento is not None:
            resultado = _serializar_reserva(conexion, reintento)
            conexion.rollback()
            return resultado, False
        if vigentes:
            conexion.rollback()
            return _butaca_no_disponible()

        vencidas = {
            item["reserva_id"]
            for item in ocupaciones
            if item.get("reserva_id") and not item.get("vigente")
        }
        marcar_reservas_vencidas(conexion, vencidas)

        reserva_id = str(uuid.uuid4())
        insertar_reserva(conexion, reserva_id, usuario_id, funcion_id)
        retener_butacas(conexion, reserva_id, funcion_id, butaca_ids)
        reserva = buscar_reserva(conexion, reserva_id)
        resultado = _serializar_reserva(conexion, reserva)
        conexion.commit()
        return resultado, True
    except IntegrityError:
        conexion.rollback()
        return _butaca_no_disponible()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def obtener_reserva(reserva_id, usuario_id):
    conexion = get_db_connection()
    try:
        reserva = buscar_reserva(conexion, reserva_id)
        if reserva is None:
            return _reserva_no_encontrada()
        if int(reserva["usuario_id"]) != usuario_id:
            return _reserva_ajena()
        if (
            reserva["estado"] in {"retenida", "pago_en_proceso"}
            and not reserva["vigente"]
        ):
            return _reserva_vencida()
        return _serializar_reserva(conexion, reserva)
    finally:
        conexion.close()


def obtener_reserva_activa(usuario_id):
    conexion = get_db_connection()
    try:
        reserva = buscar_reserva_activa_usuario(conexion, usuario_id)
        if reserva is None:
            return None
        return _serializar_reserva(conexion, reserva)
    finally:
        conexion.close()


def cancelar_reserva(reserva_id, usuario_id):
    conexion = get_db_connection()
    try:
        inicial = buscar_reserva(conexion, reserva_id)
        if inicial is None:
            return _reserva_no_encontrada()

        conexion.rollback()
        conexion.start_transaction()
        buscar_funcion_para_compra(conexion, inicial["funcion_id"])
        reserva = buscar_reserva(conexion, reserva_id, bloquear=True)
        if int(reserva["usuario_id"]) != usuario_id:
            conexion.rollback()
            return _reserva_ajena()
        if reserva["estado"] == "pago_en_proceso":
            conexion.rollback()
            return respuesta_error(
                409,
                "PAGO_EN_PROCESO",
                "La reserva no se puede cancelar",
                "El pago pendiente debe ser conciliado antes de liberar las butacas.",
            )
        if reserva["estado"] != "retenida" or not reserva["vigente"]:
            conexion.rollback()
            return _reserva_vencida()

        butacas = listar_butacas_reserva(conexion, reserva_id, bloquear=True)
        resultado = _serializar_reserva(conexion, reserva, butacas)
        cancelar_reserva_repository(conexion, reserva_id)
        liberar_butacas_reserva(conexion, reserva_id)
        resultado["estado"] = "cancelada"
        conexion.commit()
        return resultado
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def iniciar_pago(reserva_id, usuario_id, datos, idempotencia):
    conexion = get_db_connection()
    try:
        inicial = buscar_reserva(conexion, reserva_id)
        if inicial is None:
            return _reserva_no_encontrada()

        conexion.rollback()
        conexion.start_transaction()
        funcion = buscar_funcion_para_compra(conexion, inicial["funcion_id"])
        reserva = buscar_reserva(conexion, reserva_id, bloquear=True)
        if int(reserva["usuario_id"]) != usuario_id:
            conexion.rollback()
            return _reserva_ajena()

        if reserva["estado"] in {"pago_en_proceso", "vendida"}:
            if reserva.get("idempotencia_pago") == idempotencia:
                resultado = _serializar_reserva(conexion, reserva)
                conexion.rollback()
                return resultado, False
            conexion.rollback()
            return respuesta_error(
                409,
                "PAGO_YA_INICIADO",
                "El pago ya fue iniciado",
                "Use la misma Idempotency-Key para recuperar el intento existente.",
            )
        if reserva["estado"] != "retenida" or not reserva["vigente"]:
            conexion.rollback()
            return _reserva_vencida()

        butacas = listar_butacas_reserva(conexion, reserva_id, bloquear=True)
        if not butacas or any(item["estado"] != "retenida" for item in butacas):
            conexion.rollback()
            return _butaca_no_disponible()

        servicios_preparados = _preparar_servicios(
            conexion,
            datos["servicios"],
        )
        if es_respuesta_error(servicios_preparados):
            conexion.rollback()
            return servicios_preparados
        servicios, total_servicios = servicios_preparados
        precio_entrada = int(funcion["precio"])
        total_entradas = precio_entrada * len(butacas)
        compra_id = crear_compra(
            conexion,
            usuario_id,
            reserva["funcion_id"],
            reserva_id,
            datos["medio_pago"],
            total_entradas,
            total_servicios,
            total_entradas + total_servicios,
        )
        agregar_servicios_compra(conexion, compra_id, servicios)

        iniciar_pago_reserva(
            conexion,
            reserva_id,
            idempotencia,
            compra_id,
        )
        reserva = buscar_reserva(conexion, reserva_id)
        resultado = _serializar_reserva(conexion, reserva)
        resultado["mensaje"] = (
            "El pago quedó listo para ser resuelto desde la pasarela "
            "simulada del proyecto."
        )
        conexion.commit()
        return resultado, True
    except IntegrityError:
        conexion.rollback()
        return respuesta_error(
            409,
            "CONFLICTO_PAGO",
            "No fue posible iniciar el pago",
            "El intento ya fue registrado o la reserva cambió de estado.",
        )
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def _vencer_pago(conexion, reserva_id):
    marcar_reservas_vencidas(conexion, {reserva_id})
    liberar_butacas_reserva(conexion, reserva_id)
    conexion.commit()
    return _reserva_vencida()


def simular_pago(reserva_id, usuario_id, resultado_pago):
    """Aprueba o cancela el pago ficticio dentro de una única transacción."""
    conexion = get_db_connection()
    try:
        inicial = buscar_reserva(conexion, reserva_id)
        if inicial is None:
            return _reserva_no_encontrada()
        if int(inicial["usuario_id"]) != usuario_id:
            return _reserva_ajena()

        conexion.rollback()
        conexion.start_transaction()
        funcion = buscar_funcion_para_compra(conexion, inicial["funcion_id"])
        reserva = buscar_reserva(conexion, reserva_id, bloquear=True)
        if int(reserva["usuario_id"]) != usuario_id:
            conexion.rollback()
            return _reserva_ajena()

        if reserva["estado"] == "vendida":
            if resultado_pago == "cancelado":
                conexion.rollback()
                return respuesta_error(
                    409,
                    "COMPRA_YA_CONFIRMADA",
                    "La compra ya fue confirmada",
                    "Una compra confirmada ya no se puede cancelar.",
                )
            compra = buscar_compra_por_id(conexion, reserva["compra_id"])
            resultado = _completar_compra(conexion, compra)
            conexion.rollback()
            return resultado

        if resultado_pago == "cancelado":
            if reserva["estado"] == "pago_rechazado":
                resultado = _serializar_reserva(conexion, reserva)
                conexion.rollback()
                return resultado
            if reserva["estado"] == "retenida":
                conexion.rollback()
                return respuesta_error(
                    409,
                    "PAGO_NO_INICIADO",
                    "El pago todavía no fue iniciado",
                    "Primero debe iniciar el pago de la reserva.",
                )
            if reserva["estado"] != "pago_en_proceso":
                conexion.rollback()
                return respuesta_error(
                    409,
                    "PAGO_FINALIZADO",
                    "El pago ya fue finalizado",
                    "El estado actual no admite una cancelación.",
                )
            butacas = listar_butacas_reserva(
                conexion,
                reserva["id"],
                bloquear=True,
            )
            resultado = _serializar_reserva(conexion, reserva, butacas)
            rechazar_pago_reserva(conexion, reserva["id"])
            liberar_butacas_reserva(conexion, reserva["id"])
            resultado["estado"] = "pago_rechazado"
            conexion.commit()
            return resultado

        if reserva["estado"] == "vencida":
            conexion.rollback()
            return _reserva_vencida()
        if reserva["estado"] != "pago_en_proceso":
            conexion.rollback()
            return respuesta_error(
                409,
                "PAGO_FINALIZADO",
                "El pago ya fue finalizado",
                "El estado actual no permite aprobar el pago.",
            )
        if not reserva["vigente"]:
            return _vencer_pago(conexion, reserva["id"])

        butacas = listar_butacas_reserva(
            conexion,
            reserva["id"],
            bloquear=True,
        )
        if not butacas or any(
            item["estado"] != "pago_en_proceso"
            or item["reserva_id"] != reserva["id"]
            for item in butacas
        ):
            conexion.rollback()
            return _butaca_no_disponible()

        if vender_butacas_reserva(conexion, reserva["id"]) != len(butacas):
            conexion.rollback()
            return _butaca_no_disponible()
        if confirmar_compra_repository(conexion, reserva["compra_id"]) != 1:
            conexion.rollback()
            return respuesta_error(
                409,
                "PAGO_FINALIZADO",
                "El pago ya fue finalizado",
                "La compra pendiente cambió de estado.",
            )

        precio_entrada = int(funcion["precio"])
        for butaca in butacas:
            crear_entrada(
                conexion,
                reserva["compra_id"],
                butaca["butaca_funcion_id"],
                precio_entrada,
                generar_token_qr(),
            )
        confirmar_reserva(conexion, reserva["id"])
        compra = buscar_compra_por_id(conexion, reserva["compra_id"])
        resultado = _completar_compra(conexion, compra)
        conexion.commit()
        return resultado
    except IntegrityError:
        conexion.rollback()
        return respuesta_error(
            409,
            "CONFLICTO_CONFIRMACION",
            "No fue posible confirmar el pago",
            "La compra o alguna de sus entradas ya fue procesada.",
        )
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
