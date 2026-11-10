from flask import Blueprint, jsonify, request

servicios_bp = Blueprint("servicios", __name__)

@servicios_bp.route("/servicios", methods=["GET"])
def listar_servicios():
    return "lista de servicios"

@servicios_bp.route("/servicios", methods=["POST"])
def crear_servicio():
    return "crear servicio"

@servicios_bp.route("/servicios/<int:servicio_id>", methods=["GET"])
def obtener_servicio():
    return "obtener sala id"

@servicios_bp.route("/servicios", methods=["PATCH"])
def modifica_servicio():
    return "Modificar servicio / Habilitar - Dar de baja"

@servicios_bp.route("/servicios", methods=["DELETE"])
def borrar_servicio():
    return "borrar servicio"



# TESTEO #

servicios_prueba = [
    {
        "id": 1,
        "nombre": "Combo clásico",
        "descripcion": "Pochoclos y bebida mediana.",
        "precio": 5500.0,
        "activo": True,
    },
    {
        "id": 2,
        "nombre": "Bebida grande",
        "descripcion": "Gaseosa grande, sabor a elección.",
        "precio": 3200.0,
        "activo": True,
    },
]

