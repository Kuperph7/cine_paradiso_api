from unittest.mock import Mock

from app import create_app


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"


def test_listar_servicios_publicos(monkeypatch):
    servicio = {
        "id": 1,
        "nombre": "Combo Paradiso",
        "descripcion": "Pochoclos y gaseosas",
        "precio": 14800,
        "activo": True,
    }
    listar = Mock(return_value={"servicios": [servicio]})
    monkeypatch.setattr("app.routes.servicios.listar_servicios_service", listar)

    cliente = create_app(TestConfig).test_client()
    respuesta = cliente.get("/servicios")

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"servicios": [servicio]}
    listar.assert_called_once_with(incluir_inactivos=False)


def test_filtro_inactivos_requiere_administrador(monkeypatch):
    listar = Mock()
    monkeypatch.setattr("app.routes.servicios.listar_servicios_service", listar)

    cliente = create_app(TestConfig).test_client()
    respuesta = cliente.get("/servicios?incluir_inactivos=true")

    assert respuesta.status_code == 403
    listar.assert_not_called()


def test_filtro_inactivos_invalido_devuelve_400():
    cliente = create_app(TestConfig).test_client()
    respuesta = cliente.get("/servicios?incluir_inactivos=si")

    assert respuesta.status_code == 400
    assert respuesta.get_json()["codigo"] == "FILTRO_INVALIDO"
