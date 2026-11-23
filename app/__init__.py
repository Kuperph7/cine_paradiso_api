
from flask import Flask

from app import config
from app.errors import registrar_manejadores_errores
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.cartelera import cartelera_bp
from app.routes.compras import compras_bp
from app.routes.entradas import entradas_bp
from app.routes.reservas import reservas_bp
from app.routes.salas import salas_bp
from app.routes.servicios import servicios_bp
from app.routes.categorias import categorias_bp
from app.routes.health import health_bp

def create_app(config_values=None):
    app = Flask(__name__)

    # La configuración normal proviene del módulo config y sus variables de
    # entorno. Los tests pueden reemplazar valores puntuales con un diccionario,
    # sin definir clases de configuración.
    app.config.from_object(config)
    if config_values:
        app.config.update(config_values)

    app.register_blueprint(auth_bp)
    app.register_blueprint(cartelera_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(entradas_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(salas_bp)
    app.register_blueprint(servicios_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(health_bp)
    registrar_manejadores_errores(app)

    return app

