from datetime import datetime, timedelta

import jwt
import pytest
from mysql.connector import IntegrityError

from app import create_app
from app.errors import respuesta_error
from app.services import auth_service, compras_service, entradas_service


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test-secret-with-at-least-32-bytes"


@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


def _authorization(role):
    token = jwt.encode(
        {"usuario_id": 1, "email": "test@example.com", "rol": role},
        TestConfig.SECRET_KEY,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _assert_error(response, status, code):
    assert response.status_code == status
    assert response.content_type == "application/json"

    body = response.get_json()
    assert set(body) == {"codigo", "mensaje", "detalles"}
    assert body["codigo"] == code
    assert isinstance(body["mensaje"], str) and body["mensaje"]
    assert body["detalles"]
    assert set(body["detalles"][0]) == {"campo", "mensaje"}


@pytest.mark.parametrize("status", [400, 401, 403, 404, 409])
def test_api_errors_share_the_same_contract(status):
    body, returned_status = respuesta_error(
        status,
        f"ERROR_{status}",
        "Mensaje",
        "Detalle",
    )

    assert returned_status == status
    assert set(body) == {"codigo", "mensaje", "detalles"}
    assert body["codigo"] == f"ERROR_{status}"
    assert body["mensaje"] == "Mensaje"
    assert body["detalles"] == [
        {"campo": "general", "mensaje": "Detalle"}
    ]


def test_malformed_json_is_a_uniform_validation_error(client):
    response = client.post(
        "/auth/register",
        data='{"nombre":',
        content_type="application/json",
    )

    _assert_error(response, 400, "DATOS_INVALIDOS")


def test_invalid_field_types_are_validation_errors(client):
    response = client.post(
        "/auth/register",
        json={
            "nombre": 123,
            "email": "ana@example.com",
            "password": "123456",
        },
    )

    _assert_error(response, 400, "DATOS_INVALIDOS")


def test_missing_authentication_is_uniform(client):
    response = client.get("/mis-entradas")

    _assert_error(response, 401, "AUTENTICACION_REQUERIDA")


def test_insufficient_permissions_are_uniform(client):
    response = client.get("/salas", headers=_authorization("cliente"))

    _assert_error(response, 403, "PERMISO_DENEGADO")


def test_unknown_routes_are_uniform(client):
    response = client.get("/recurso-inexistente")

    _assert_error(response, 404, "RECURSO_NO_ENCONTRADO")


def test_duplicate_email_precheck_is_uniform(client, monkeypatch):
    monkeypatch.setattr(
        auth_service.usuarios_repository,
        "obtener_usuario_por_email",
        lambda email: {"id": 1, "email": email},
    )

    response = client.post(
        "/auth/register",
        json={
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "123456",
        },
    )

    _assert_error(response, 409, "CONFLICTO_EMAIL")


def test_duplicate_email_database_race_is_mapped_to_conflict(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        auth_service.usuarios_repository,
        "obtener_usuario_por_email",
        lambda email: None,
    )

    def duplicate_email(**kwargs):
        raise IntegrityError("Duplicate entry")

    monkeypatch.setattr(
        auth_service.usuarios_repository,
        "crear_usuario",
        duplicate_email,
    )

    response = client.post(
        "/auth/register",
        json={
            "nombre": "Ana",
            "email": "ana@example.com",
            "password": "123456",
        },
    )

    _assert_error(response, 409, "CONFLICTO_EMAIL")


def test_unavailable_show_is_an_availability_conflict():
    show = {
        "estado": "cancelada",
        "sala_activa": True,
        "pelicula_activa": True,
        "fecha_hora": datetime.now(compras_service.ZONA_HORARIA)
        + timedelta(days=1),
    }

    body, status = compras_service._validar_funcion(show)

    assert status == 409
    assert body["codigo"] == "FUNCION_NO_DISPONIBLE"


def test_invalid_ticket_is_returned_with_a_specific_reason(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        entradas_service.entradas_repository,
        "obtener_entrada_por_qr",
        lambda codigo_qr, funcion_id: None,
    )

    response = client.post(
        "/admin/entradas/validar",
        headers=_authorization("administrador"),
        json={"codigo_qr": "qr-inexistente", "funcion_id": 1},
    )

    _assert_error(response, 404, "ENTRADA_NO_ENCONTRADA")
