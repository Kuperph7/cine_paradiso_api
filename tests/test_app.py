from app import create_app


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"


def test_create_app():
    app = create_app(TestConfig)

    assert app.testing is True


def test_ruta_butacas_respeta_swagger():
    app = create_app(TestConfig)
    rutas = {regla.rule for regla in app.url_map.iter_rules()}

    assert "/funciones/<int:funcion_id>/butacas" in rutas
    assert "/cartelera/funciones/<int:funcion_id>/butacas" not in rutas
    assert "/funciones/<int:funcion_id>" in rutas
    assert "/peliculas/<int:pelicula_id>" in rutas

