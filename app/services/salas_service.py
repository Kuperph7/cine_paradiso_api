"""Servicios de gestión administrativa de salas y butacas."""

from mysql.connector import IntegrityError

from app.db import get_db_connection
from app.errors import ApiError
from app.repositories.salas_repository import (
    activar_butacas,
    actualizar_sala as guardar_cambios_sala,
    buscar_local_por_id,
    buscar_sala_por_id,
    crear_butacas,
    crear_sala as insertar_sala,
    desactivar_butacas_de_sala,
    existe_sala_con_nombre,
    listar_butacas_de_sala,
    listar_salas as consultar_salas_repository,
)


def _serializar_sala(sala):
    resultado = dict(sala)
    for campo in ("id", "local_id", "filas", "butacas_por_fila", "capacidad"):
        resultado[campo] = int(resultado[campo])
    resultado["activa"] = bool(resultado["activa"])
    return resultado


def _nombre_fila(numero_fila):
    nombre = ""
    while numero_fila:
        numero_fila, resto = divmod(numero_fila - 1, 26)
        nombre = chr(65 + resto) + nombre
    return nombre


def _generar_coordenadas(filas, butacas_por_fila):
    return [
        (_nombre_fila(numero_fila), numero_butaca)
        for numero_fila in range(1, filas + 1)
        for numero_butaca in range(1, butacas_por_fila + 1)
    ]


def _validar_local(conexion, local_id):
    local = buscar_local_por_id(conexion, local_id)
    if local is None:
        raise ApiError(
            404,
            "LOCAL_NO_ENCONTRADO",
            "Local no encontrado",
            "No existe un local con ese identificador.",
        )
    if not local["activa"]:
        raise ApiError(
            409,
            "LOCAL_INACTIVO",
            "Local inactivo",
            "No se puede habilitar una sala en un local inactivo.",
        )


def _validar_nombre_disponible(
    conexion,
    local_id,
    nombre,
    excluir_id=None,
):
    if existe_sala_con_nombre(conexion, local_id, nombre, excluir_id):
        raise ApiError(
            409,
            "SALA_DUPLICADA",
            "Sala ya registrada",
            "Ya existe una sala con ese nombre en el local.",
        )


def _sincronizar_butacas(conexion, sala_id, filas, butacas_por_fila):
    coordenadas = _generar_coordenadas(filas, butacas_por_fila)
    existentes = {
        (butaca["fila"], int(butaca["numero"])): butaca["id"]
        for butaca in listar_butacas_de_sala(conexion, sala_id)
    }

    desactivar_butacas_de_sala(conexion, sala_id)
    ids_a_activar = [
        existentes[coordenada]
        for coordenada in coordenadas
        if coordenada in existentes
    ]
    nuevas = [
        coordenada for coordenada in coordenadas if coordenada not in existentes
    ]
    activar_butacas(conexion, ids_a_activar)
    crear_butacas(conexion, sala_id, nuevas)


def _conflicto_sala():
    return ApiError(
        409,
        "CONFLICTO_SALA",
        "No fue posible guardar la sala",
        "La sala entra en conflicto con los datos existentes.",
    )


def listar_salas(incluir_inactivas=False):
    conexion = get_db_connection()
    try:
        salas = consultar_salas_repository(conexion, incluir_inactivas)
        return {"salas": [_serializar_sala(sala) for sala in salas]}
    finally:
        conexion.close()


def crear_sala(datos):
    conexion = get_db_connection()
    try:
        _validar_local(conexion, datos["local_id"])
        _validar_nombre_disponible(
            conexion,
            datos["local_id"],
            datos["nombre"],
        )

        sala_id = insertar_sala(conexion, datos)
        coordenadas = _generar_coordenadas(
            datos["filas"],
            datos["butacas_por_fila"],
        )
        crear_butacas(conexion, sala_id, coordenadas)
        sala = buscar_sala_por_id(conexion, sala_id)
        conexion.commit()
        return _serializar_sala(sala)
    except IntegrityError as error:
        conexion.rollback()
        raise _conflicto_sala() from error
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def actualizar_sala(sala_id, cambios):
    conexion = get_db_connection()
    try:
        sala_actual = buscar_sala_por_id(conexion, sala_id, bloquear=True)
        if sala_actual is None:
            raise ApiError(
                404,
                "SALA_NO_ENCONTRADA",
                "Sala no encontrada",
                "No existe una sala con ese identificador.",
            )

        if cambios.get("activa") is True:
            _validar_local(conexion, sala_actual["local_id"])
        if "nombre" in cambios:
            _validar_nombre_disponible(
                conexion,
                sala_actual["local_id"],
                cambios["nombre"],
                excluir_id=sala_id,
            )

        distribucion_cambia = (
            "filas" in cambios
            and cambios["filas"] != sala_actual["filas"]
        ) or (
            "butacas_por_fila" in cambios
            and cambios["butacas_por_fila"] != sala_actual["butacas_por_fila"]
        )

        guardar_cambios_sala(conexion, sala_id, cambios)
        if distribucion_cambia:
            filas = cambios.get("filas", sala_actual["filas"])
            butacas_por_fila = cambios.get(
                "butacas_por_fila",
                sala_actual["butacas_por_fila"],
            )
            _sincronizar_butacas(conexion, sala_id, filas, butacas_por_fila)

        sala = buscar_sala_por_id(conexion, sala_id)
        conexion.commit()
        return _serializar_sala(sala)
    except IntegrityError as error:
        conexion.rollback()
        raise _conflicto_sala() from error
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()
