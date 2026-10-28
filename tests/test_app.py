from app import create_app


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"


def test_create_app():
    app = create_app(TestConfig)

    assert app.testing is True

