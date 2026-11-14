from decimal import Decimal

import pytest
from app.validators.admin_validators import (
    validate_function_state,
    validate_service_price,
)
from app.validators.auth_validators import validate_role
from app.validators.compras_validators import (
    validar_creacion_reserva,
    validar_inicio_pago,
    validar_pago_simulado,
    validate_purchase_total,
    validate_seat_state,
    validate_service_line,
)


def test_valid_business_values():
    assert validate_role("cliente") == "cliente"
    assert validate_function_state("programada") == "programada"
    assert validate_seat_state("disponible") == "disponible"
    assert validate_service_price(Decimal("4500.00")) == Decimal("4500.00")
    assert validate_purchase_total(0) == 0
    assert validate_service_line(2, 1500, 3000) == (2, 1500, 3000)


@pytest.mark.parametrize(
    ("validator", "value"),
    [
        (validate_role, "superusuario"),
        (validate_function_state, "finalizada"),
        (validate_seat_state, "bloqueada"),
        (validate_service_price, -1),
        (validate_purchase_total, -1),
    ],
)
def test_invalid_business_values_return_uniform_error(validator, value):
    body, status = validator(value)

    assert status == 400
    assert body["codigo"] == "DATOS_INVALIDOS"


def test_invalid_service_quantity_returns_uniform_error():
    body, status = validate_service_line(0, 1500, 0)

    assert status == 400
    assert body["codigo"] == "DATOS_INVALIDOS"


def test_validadores_del_flujo_de_reserva_y_pago():
    assert validar_creacion_reserva({"butaca_ids": [1, 2]}) == {
        "butaca_ids": [1, 2]
    }
    assert validar_inicio_pago({"medio_pago": "tarjeta"}) == {
        "medio_pago": "tarjeta",
        "servicios": [],
    }
    assert validar_pago_simulado({"resultado": "aprobado"}) == {
        "resultado": "aprobado"
    }
