from flask import Flask

from app.config import Config
from app.errors import ApiError, error_response
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.cartelera import cartelera_bp
from app.routes.compras import compras_bp
from app.routes.entradas import entradas_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.register_blueprint(auth_bp)
    app.register_blueprint(cartelera_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(entradas_bp)
    app.register_blueprint(admin_bp)
    app.register_error_handler(ApiError, error_response)

    return app

