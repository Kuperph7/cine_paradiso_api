"""Servicios de compras, cancelaciones y butacas."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from mysql.connector import IntegrityError

from app.db import get_db_connection
from app.errors import es_respuesta_error, respuesta_error
from app.integrations.qr import generar_token_qr
from app.repositories.compras_repository import (
    agregar_servicios_compra,
    bloquear_butacas,
    buscar_butacas_funcion,
    buscar_compra_por_id,
    buscar_ocupaciones_butacas,
    cancelar_compra as guardar_cancelacion_compra,
    crear_compra as insertar_compra,
    liberar_butacas_compra,
    listar_compras as consultar_compras_repository,
    listar_servicios_compra,
    ocupar_butacas,
)
from app.repositories.entradas_repository import (
    bloquear_entradas_compra,
    cancelar_entradas_compra,
    crear_entrada,
    listar_entradas_compra,
)
from app.repositories.funciones_repository import buscar_funcion_para_compra
from app.repositories.servicios_repository import buscar_servicios_por_ids


ZONA_HORARIA = ZoneInfo("America/Argentina/Buenos_Aires")
PLAZO_CANCELACION = timedelta(hours=1)


def _fecha_local(fecha):
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=ZONA_HORARIA)
    return fecha.astimezone(ZONA_HORARIA)


def _fecha_iso(fecha):
    return _fecha_local(fecha).isoformat() if fecha is not None else None


def _serializar_servicio(servicio):
    resultado = dict(servicio)
    for campo in ("servicio_id", "cantidad", "precio_unitario", "subtotal"):
        resultado[campo] = int(resultado[campo])
    return resultado


def _serializar_entrada(entrada):
    estado_butaca = entrada["estado_butaca"]
    if estado_butaca != "disponible":
        estado_butaca = "ocupada"

    return {
        "id": int(entrada["id"]),
        "compra_id": int(entrada["compra_id"]),
        "usuario_id": int(entrada["usuario_id"]),
        "funcion_id": int(entrada["funcion_id"]),
        "butaca": {
            "id": int(entrada["butaca_id"]),
            "fila": entrada["fila"],
            "numero": int(entrada["numero"]),
            "estado": estado_butaca,
        },
        "codigo_qr": entrada["codigo_qr"],
        "estado": entrada["estado"],
        "utilizada_en": _fecha_iso(entrada.get("utilizada_en")),
    }


def _completar_compra(conexion, compra):
    resultado = dict(compra)
    resultado.pop("funcion_fecha_hora", None)
    for campo in (
        "id",
        "usuario_id",
        "funcion_id",
        "total_entradas",
        "total_servicios",
        "total",
    ):
        resultado[campo] = int(resultado[campo])
    resultado["fecha_hora"] = _fecha_iso(resultado["fecha_hora"])
    resultado["servicios"] = [
        _serializar_servicio(servicio)
        for servicio in listar_servicios_compra(conexion, resultado["id"])
    ]
    resultado["entradas"] = [
        _serializar_entrada(entrada)
        for entrada in listar_entradas_compra(conexion, resultado["id"])
    ]
    return resultado


def _validar_pertenencia(compra, usuario_id, es_administrador):
    if not es_administrador and compra["usuario_id"] != usuario_id:
        return respuesta_error(
            403,
            "COMPRA_AJENA",
            "Permiso denegado",
            "La compra no pertenece al usuario autenticado.",
        )


def _validar_funcion(funcion):
    if funcion is None:
        return respuesta_error(
            404,
            "FUNCION_NO_ENCONTRADA",
            "Función no encontrada",
            "No existe una función con ese identificador.",
        )

    fecha_hora = _fecha_local(funcion["fecha_hora"])
    if (
        funcion["estado"] != "programada"
        or not funcion["sala_activa"]
        or not funcion["pelicula_activa"]
        or fecha_hora <= datetime.now(ZONA_HORARIA)
    ):
        return respuesta_error(
            409,
            "FUNCION_NO_DISPONIBLE",
            "Función no disponible",
            "La función ya no admite compras.",
        )


def _validar_y_bloquear_butacas(conexion, funcion, butaca_ids):
    butacas = bloquear_butacas(conexion, funcion["sala_id"], butaca_ids)
    encontradas = {int(butaca["id"]) for butaca in butacas}
    if encontradas != set(butaca_ids):
        return respuesta_error(
            404,
            "BUTACA_NO_ENCONTRADA",
            "Butaca no encontrada",
            "Una o más butacas no existen, están inactivas o pertenecen a otra sala.",
        )

    ahora = datetime.now(ZONA_HORARIA)
    ocupaciones = buscar_ocupaciones_butacas(
        conexion,
        funcion["id"],
        butaca_ids,
    )
    for ocupacion in ocupaciones:
        reservada = ocupacion["estado"] == "reservada"
        reserva_hasta = ocupacion.get("reserva_hasta")
        reserva_vigente = reserva_hasta is None or _fecha_local(reserva_hasta) > ahora
        if ocupacion["estado"] == "ocupada" or (reservada and reserva_vigente):
            return respuesta_error(
                409,
                "BUTACA_NO_DISPONIBLE",
                "Butaca no disponible",
                "Una de las butacas seleccionadas ya está reservada u ocupada.",
            )


def _preparar_servicios(conexion, seleccionados):
    if not seleccionados:
        return [], 0

    cantidades = {
        servicio["servicio_id"]: servicio["cantidad"]
        for servicio in seleccionados
    }
    servicios = buscar_servicios_por_ids(conexion, list(cantidades))
    encontrados = {int(servicio["id"]) for servicio in servicios}
    if encontrados != set(cantidades):
        return respuesta_error(
            404,
            "SERVICIO_NO_ENCONTRADO",
            "Servicio no encontrado",
            "Uno o más servicios no existen.",
        )

    preparados = []
    total = 0
    for servicio in servicios:
        if not servicio["activo"]:
            return respuesta_error(
                409,
                "SERVICIO_INACTIVO",
                "Servicio no disponible",
                "Uno de los servicios seleccionados está inactivo.",
            )
        servicio_id = int(servicio["id"])
        cantidad = cantidades[servicio_id]
        precio = int(servicio["precio"])
        subtotal = precio * cantidad
        total += subtotal
        preparados.append(
            {
                "servicio_id": servicio_id,
                "cantidad": cantidad,
                "precio_unitario": precio,
                "subtotal": subtotal,
            }
        )
    return preparados, total


def _conflicto_compra():
    return respuesta_error(
        409,
        "CONFLICTO_COMPRA",
        "No fue posible completar la compra",
        "La disponibilidad cambió mientras se procesaba la operación.",
    )


def crear_compra(usuario_id, datos):
    conexion = get_db_connection()
    try:
        conexion.start_transaction()
        funcion = buscar_funcion_para_compra(conexion, datos["funcion_id"])
        error = _validar_funcion(funcion)
        if es_respuesta_error(error):
            conexion.rollback()
            return error
        error = _validar_y_bloquear_butacas(
            conexion,
            funcion,
            datos["butaca_ids"],
        )
        if es_respuesta_error(error):
            conexion.rollback()
            return error
        servicios_preparados = _preparar_servicios(
            conexion,
            datos["servicios"],
        )
        if es_respuesta_error(servicios_preparados):
            conexion.rollback()
            return servicios_preparados
        servicios, total_servicios = servicios_preparados

        precio_entrada = int(funcion["precio"])
        total_entradas = precio_entrada * len(datos["butaca_ids"])
        total = total_entradas + total_servicios
        compra_id = insertar_compra(
            conexion,
            usuario_id,
            funcion["id"],
            datos["medio_pago"],
            total_entradas,
            total_servicios,
            total,
        )
        agregar_servicios_compra(conexion, compra_id, servicios)

        ocupar_butacas(conexion, funcion["id"], datos["butaca_ids"])
        butacas_funcion = buscar_butacas_funcion(
            conexion,
            funcion["id"],
            datos["butaca_ids"],
        )
        ids_por_butaca = {
            int(butaca["butaca_id"]): int(butaca["id"])
            for butaca in butacas_funcion
        }
        if set(ids_por_butaca) != set(datos["butaca_ids"]):
            conexion.rollback()
            return _conflicto_compra()

        for butaca_id in datos["butaca_ids"]:
            crear_entrada(
                conexion,
                compra_id,
                ids_por_butaca[butaca_id],
                precio_entrada,
                generar_token_qr(),
            )

        compra = buscar_compra_por_id(conexion, compra_id)
        resultado = _completar_compra(conexion, compra)
        conexion.commit()
        return resultado
    except IntegrityError:
        conexion.rollback()
        return _conflicto_compra()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_compras(usuario_id, es_administrador, filtros):
    conexion = get_db_connection()
    try:
        usuario_filtro = filtros["usuario_id"] if es_administrador else usuario_id
        compras = consultar_compras_repository(
            conexion,
            usuario_filtro,
            filtros["estado"],
        )
        return {
            "compras": [_completar_compra(conexion, compra) for compra in compras]
        }
    finally:
        conexion.close()


def obtener_compra(compra_id, usuario_id, es_administrador):
    conexion = get_db_connection()
    try:
        compra = buscar_compra_por_id(conexion, compra_id)
        if compra is None:
            return respuesta_error(
                404,
                "COMPRA_NO_ENCONTRADA",
                "Compra no encontrada",
                "No existe una compra con ese identificador.",
            )
        error = _validar_pertenencia(compra, usuario_id, es_administrador)
        if es_respuesta_error(error):
            return error
        return _completar_compra(conexion, compra)
    finally:
        conexion.close()


def cancelar_compra(compra_id, usuario_id, es_administrador, motivo=None):
    conexion = get_db_connection()
    try:
        conexion.start_transaction()
        compra = buscar_compra_por_id(conexion, compra_id, bloquear=True)
        if compra is None:
            conexion.rollback()
            return respuesta_error(
                404,
                "COMPRA_NO_ENCONTRADA",
                "Compra no encontrada",
                "No existe una compra con ese identificador.",
            )
        error = _validar_pertenencia(compra, usuario_id, es_administrador)
        if es_respuesta_error(error):
            conexion.rollback()
            return error

        if compra["estado"] != "confirmada":
            conexion.rollback()
            return respuesta_error(
                409,
                "COMPRA_YA_CANCELADA",
                "Compra no cancelable",
                "La compra ya se encuentra cancelada.",
            )

        inicio_funcion = _fecha_local(compra["funcion_fecha_hora"])
        if inicio_funcion <= datetime.now(ZONA_HORARIA) + PLAZO_CANCELACION:
            conexion.rollback()
            return respuesta_error(
                409,
                "PLAZO_CANCELACION_VENCIDO",
                "Compra no cancelable",
                "La cancelación debe solicitarse al menos una hora antes "
                "de la función.",
            )

        entradas = bloquear_entradas_compra(conexion, compra_id)
        if any(entrada["estado"] == "utilizada" for entrada in entradas):
            conexion.rollback()
            return respuesta_error(
                409,
                "ENTRADA_YA_UTILIZADA",
                "Compra no cancelable",
                "La compra contiene una entrada que ya fue utilizada.",
            )

        guardar_cancelacion_compra(conexion, compra_id, motivo)
        cancelar_entradas_compra(conexion, compra_id)
        liberar_butacas_compra(conexion, compra_id)
        compra = buscar_compra_por_id(conexion, compra_id)
        resultado = _completar_compra(conexion, compra)
        conexion.commit()
        return resultado
    except IntegrityError:
        conexion.rollback()
        return _conflicto_compra()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

