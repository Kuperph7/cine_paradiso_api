"""Pruebas de integracion: requieren el MySQL/InnoDB de Docker Compose."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from app import create_app
from app.db import get_db_connection
from app.security import generar_token_acceso


FUNCION_ID = 102


@pytest.fixture(scope="module")
def app_mysql():
    app = create_app()
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-with-at-least-32-bytes-long",
    )
    return app


def _limpiar_funcion(app):
    with app.app_context():
        conexion = get_db_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "UPDATE reservas SET compra_id = NULL WHERE funcion_id = %s",
                (FUNCION_ID,),
            )
            cursor.execute(
                """
                DELETE e FROM entradas AS e
                INNER JOIN compras AS c ON c.id = e.compra_id
                WHERE c.funcion_id = %s
                """,
                (FUNCION_ID,),
            )
            cursor.execute(
                """
                DELETE cs FROM compras_servicios AS cs
                INNER JOIN compras AS c ON c.id = cs.compra_id
                WHERE c.funcion_id = %s
                """,
                (FUNCION_ID,),
            )
            cursor.execute(
                "UPDATE compras SET reserva_id = NULL WHERE funcion_id = %s",
                (FUNCION_ID,),
            )
            cursor.execute("DELETE FROM compras WHERE funcion_id = %s", (FUNCION_ID,))
            cursor.execute(
                """
                UPDATE butacas_funcion
                SET estado = 'disponible', reserva_hasta = NULL, reserva_id = NULL
                WHERE funcion_id = %s
                """,
                (FUNCION_ID,),
            )
            cursor.execute("DELETE FROM reservas WHERE funcion_id = %s", (FUNCION_ID,))
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()


@pytest.fixture(autouse=True)
def funcion_limpia(app_mysql):
    _limpiar_funcion(app_mysql)
    yield
    _limpiar_funcion(app_mysql)


@pytest.fixture(scope="module")
def butaca_ids(app_mysql):
    with app_mysql.app_context():
        conexion = get_db_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                "SELECT id FROM butacas WHERE sala_id = 1 ORDER BY id LIMIT 6"
            )
            return [fila[0] for fila in cursor.fetchall()]
        finally:
            cursor.close()
            conexion.close()


@pytest.fixture(scope="module")
def headers_usuarios(app_mysql):
    with app_mysql.app_context():
        token_1 = generar_token_acceso(
            {"id": 1, "email": "cliente@cineparadiso.local", "rol": "cliente"}
        )
        token_2 = generar_token_acceso(
            {"id": 2, "email": "admin@cineparadiso.local", "rol": "administrador"}
        )
    return (
        {"Authorization": f"Bearer {token_1}"},
        {"Authorization": f"Bearer {token_2}"},
    )


def _reservar(app, headers, butacas):
    with app.test_client() as cliente:
        return cliente.post(
            f"/funciones/{FUNCION_ID}/reservas",
            json={"butaca_ids": butacas},
            headers=headers,
        )


def _vencer_reserva(app, reserva_id):
    with app.app_context():
        conexion = get_db_connection()
        cursor = conexion.cursor()
        try:
            cursor.execute(
                """
                UPDATE reservas
                SET expira_en = UTC_TIMESTAMP() - INTERVAL 1 SECOND
                WHERE id = %s
                """,
                (reserva_id,),
            )
            cursor.execute(
                """
                UPDATE butacas_funcion
                SET reserva_hasta = UTC_TIMESTAMP() - INTERVAL 1 SECOND
                WHERE reserva_id = %s
                """,
                (reserva_id,),
            )
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()


def _iniciar_pago(cliente, headers, reserva_id, clave="pago-1"):
    return cliente.post(
        f"/reservas/{reserva_id}/pagos",
        json={"medio_pago": "tarjeta", "servicios": []},
        headers={**headers, "Idempotency-Key": clave},
    )


def _simular_pago(cliente, headers, reserva_id, resultado):
    return cliente.post(
        f"/reservas/{reserva_id}/pagos/simular",
        json={"resultado": resultado},
        headers=headers,
    )


def test_dos_usuarios_concurrentes_solo_obtienen_una_reserva(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    barrera = Barrier(2)

    def intento(headers):
        barrera.wait()
        respuesta = _reservar(app_mysql, headers, [butaca_ids[0]])
        return respuesta.status_code

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        estados = list(ejecutor.map(intento, headers_usuarios))

    assert sorted(estados) == [201, 409]


def test_reserva_vigente_bloquea_y_vencida_se_puede_retomar(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]])
    assert reserva.status_code == 201
    assert _reservar(app_mysql, headers_usuarios[1], [butaca_ids[0]]).status_code == 409

    _vencer_reserva(app_mysql, reserva.json["id"])
    assert _reservar(app_mysql, headers_usuarios[1], [butaca_ids[0]]).status_code == 201


def test_consultar_o_repetir_no_renueva_la_reserva(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    primera = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]])
    expira_en = primera.json["expira_en"]
    with app_mysql.test_client() as cliente:
        consulta = cliente.get(
            f"/reservas/{primera.json['id']}",
            headers=headers_usuarios[0],
        )
    repetida = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]])

    assert consulta.status_code == 200
    assert repetida.status_code == 200
    assert consulta.json["expira_en"] == expira_en
    assert repetida.json["id"] == primera.json["id"]
    assert repetida.json["expira_en"] == expira_en


def test_seleccion_multiple_es_todo_o_nada(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    assert _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).status_code == 201
    conflicto = _reservar(
        app_mysql,
        headers_usuarios[1],
        [butaca_ids[0], butaca_ids[1]],
    )
    assert conflicto.status_code == 409
    assert _reservar(app_mysql, headers_usuarios[1], [butaca_ids[1]]).status_code == 201


def test_no_se_puede_consultar_ni_cancelar_una_reserva_ajena(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).json
    with app_mysql.test_client() as cliente:
        assert cliente.get(
            f"/reservas/{reserva['id']}", headers=headers_usuarios[1]
        ).status_code == 403
        assert cliente.delete(
            f"/reservas/{reserva['id']}", headers=headers_usuarios[1]
        ).status_code == 403


def test_compra_confirmada_e_idempotencia_impiden_duplicados(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).json
    with app_mysql.test_client() as cliente:
        assert _iniciar_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
        ).status_code == 202
        primera = _simular_pago(
            cliente, headers_usuarios[0], reserva["id"], "aprobado"
        )
        segunda = _simular_pago(
            cliente, headers_usuarios[0], reserva["id"], "aprobado"
        )

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert segunda.json["id"] == primera.json["id"]
    assert len(primera.json["entradas"]) == 1
    assert len(segunda.json["entradas"]) == 1
    assert _reservar(app_mysql, headers_usuarios[1], [butaca_ids[0]]).status_code == 409


def test_pago_simulado_confirma_la_compra_y_emite_entradas(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).json
    with app_mysql.test_client() as cliente:
        assert _iniciar_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
        ).status_code == 202
        activa = cliente.get(
            "/reservas/activa",
            headers=headers_usuarios[0],
        )
        compra = _simular_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
            "aprobado",
        )
        repetida = _simular_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
            "aprobado",
        )

    assert activa.status_code == 200
    assert activa.json["reserva"]["id"] == reserva["id"]
    assert activa.json["reserva"]["estado"] == "pago_en_proceso"
    assert compra.status_code == 200
    assert compra.json["estado"] == "confirmada"
    assert len(compra.json["entradas"]) == 1
    assert repetida.status_code == 200
    assert repetida.json["id"] == compra.json["id"]


def test_cancelar_pago_simulado_libera_las_butacas(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).json
    with app_mysql.test_client() as cliente:
        assert _iniciar_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
        ).status_code == 202
        cancelada = _simular_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
            "cancelado",
        )

    assert cancelada.status_code == 200
    assert cancelada.json["estado"] == "pago_rechazado"
    assert _reservar(
        app_mysql,
        headers_usuarios[1],
        [butaca_ids[0]],
    ).status_code == 201


def test_pago_tardio_no_sobrescribe_una_nueva_reserva(
    app_mysql,
    headers_usuarios,
    butaca_ids,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).json
    with app_mysql.test_client() as cliente:
        assert _iniciar_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
        ).status_code == 202
    _vencer_reserva(app_mysql, reserva["id"])
    nueva = _reservar(app_mysql, headers_usuarios[1], [butaca_ids[0]])
    assert nueva.status_code == 201

    with app_mysql.test_client() as cliente:
        tardio = _simular_pago(
            cliente,
            headers_usuarios[0],
            reserva["id"],
            "aprobado",
        )
        vigente = cliente.get(
            f"/reservas/{nueva.json['id']}", headers=headers_usuarios[1]
        )
    assert tardio.status_code == 410
    assert tardio.json["codigo"] == "RESERVA_VENCIDA"
    assert vigente.status_code == 200
    assert vigente.json["estado"] == "retenida"


def test_error_al_emitir_entrada_hace_rollback(
    app_mysql,
    headers_usuarios,
    butaca_ids,
    monkeypatch,
):
    reserva = _reservar(app_mysql, headers_usuarios[0], [butaca_ids[0]]).json
    with app_mysql.test_client() as cliente:
        pago = _iniciar_pago(cliente, headers_usuarios[0], reserva["id"])

    def fallar(*_args, **_kwargs):
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr("app.services.reservas_service.crear_entrada", fallar)
    with app_mysql.test_client() as cliente:
        with pytest.raises(RuntimeError, match="fallo simulado"):
            _simular_pago(
                cliente,
                headers_usuarios[0],
                reserva["id"],
                "aprobado",
            )

    with app_mysql.app_context():
        conexion = get_db_connection()
        cursor = conexion.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT estado FROM compras WHERE id = %s",
                (pago.json["compra_id"],),
            )
            assert cursor.fetchone()["estado"] == "pendiente_pago"
            cursor.execute(
                "SELECT estado FROM butacas_funcion WHERE reserva_id = %s",
                (reserva["id"],),
            )
            assert cursor.fetchone()["estado"] == "pago_en_proceso"
            cursor.execute(
                "SELECT COUNT(*) AS cantidad FROM entradas WHERE compra_id = %s",
                (pago.json["compra_id"],),
            )
            assert cursor.fetchone()["cantidad"] == 0
        finally:
            cursor.close()
            conexion.close()
