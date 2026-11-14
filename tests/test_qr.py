from unittest.mock import Mock

from app.services import entradas_service


def test_validar_qr_vigente_permite_ingreso(monkeypatch):
    entrada = {
        "id": 10,
        "funcion_id": 7,
        "estado": "vigente",
    }

    monkeypatch.setattr(
        entradas_service.entradas_repository,
        "obtener_entrada_por_qr",
        Mock(return_value=entrada),
    )

    marcar_utilizada = Mock(return_value=1)

    monkeypatch.setattr(
        entradas_service.entradas_repository,
        "marcar_entrada_utilizada",
        marcar_utilizada,
    )

    resultado = entradas_service.validar_entrada_qr(
        "QRCINE-prueba", 7
    )

    assert resultado["estado"] == "utilizada"
    assert resultado["entrada_id"] == 10

    marcar_utilizada.assert_called_once_with(10)


def test_qr_ya_utilizado_no_permite_ingreso(monkeypatch):
    entrada = {
        "id": 10,
        "funcion_id": 7,
        "estado": "utilizada",
    }

    monkeypatch.setattr(
        entradas_service.entradas_repository,
        "obtener_entrada_por_qr",
        Mock(return_value=entrada),
    )

    marcar_utilizada = Mock()

    monkeypatch.setattr(
        entradas_service.entradas_repository,
        "marcar_entrada_utilizada",
        marcar_utilizada,
    )

    resultado = entradas_service.validar_entrada_qr(
        "QRCINE-prueba", 7
    )

    error, codigo_http = resultado

    assert codigo_http == 409
    assert error["codigo"] == "ENTRADA_YA_UTILIZADA"
    marcar_utilizada.assert_not_called()


def test_generar_imagen_qr_png():
    from app.integrations.qr import generar_imagen_qr_png

    imagen = generar_imagen_qr_png("QRCINE-prueba-123")

    assert isinstance(imagen, bytes)
    assert imagen.startswith(b"\x89PNG\r\n\x1a\n")
    assert len(imagen) > 100


def test_enviar_entradas_por_email(monkeypatch):
    from unittest.mock import MagicMock
    from app.integrations.email import enviar_entradas_por_email

    monkeypatch.setenv("SMTP_HOST", "smtp.prueba")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_FROM", "entradas@cineparadiso.test")
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_STARTTLS", raising=False)

    servidor_smtp = MagicMock()

    monkeypatch.setattr(
        "app.integrations.email.smtplib.SMTP",
        servidor_smtp,
    )

    compra = {
        "id": 15,
        "entradas": [
            {
                "id": 20,
                "codigo_qr": "QRCINE-prueba-123",
                "butaca": {"fila": "B", "numero": 7},
            }
        ],
    }

    resultado = enviar_entradas_por_email(
        "cliente@cineparadiso.test",
        compra,
    )

    assert resultado is True

    conexion = servidor_smtp.return_value.__enter__.return_value
    conexion.send_message.assert_called_once()

    mensaje = conexion.send_message.call_args.args[0]

    assert mensaje["To"] == "cliente@cineparadiso.test"
    assert "Compra #15" in mensaje["Subject"]
    assert "Butaca B7" in mensaje.get_body().get_content()

    adjuntos = list(mensaje.iter_attachments())

    assert len(adjuntos) == 1
    assert adjuntos[0].get_filename() == "entrada-20.png"
    assert adjuntos[0].get_content().startswith(b"\x89PNG\r\n\x1a\n")
