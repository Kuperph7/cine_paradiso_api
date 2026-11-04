from decimal import Decimal

import pytest

from app.errors import ApiError
from app.validators.admin_validators import (
    validate_function_state,
    validate_service_price,
)
from app.validators.auth_validators import validate_role
from app.validators.compras_validators import (
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
def test_invalid_business_values_raise_api_error(validator, value):
    with pytest.raises(ApiError) as error:
        validator(value)

    assert error.value.status == 400
    assert error.value.code == "DATOS_INVALIDOS"


def test_invalid_service_quantity_raises_api_error():
    with pytest.raises(ApiError):
        validate_service_line(0, 1500, 0)
