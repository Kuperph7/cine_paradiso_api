# Cine Paradiso API

Backend del sistema de venta de entradas de Cine Paradiso, desarrollado con
Python, Flask y MySQL.

## Preparación local

1. Crear y activar un entorno virtual de Python.
2. Instalar las dependencias con `pip install -r requirements.txt`.
3. Copiar `.env.example` como `.env` y completar la configuración local.
4. Ejecutar la aplicación con `python run.py`.

El archivo `.env` contiene datos locales y no debe subirse al repositorio.

## Organización

- `app/routes`: endpoints HTTP definidos en el contrato Swagger.
- `app/validators`: validación de los datos recibidos.
- `app/services`: reglas de negocio.
- `app/repositories`: consultas SQL parametrizadas contra MySQL.
- `app/integrations`: API de películas, correo electrónico y códigos QR.
- `sql`: creación de tablas y datos iniciales.
- `tests`: pruebas automatizadas.
- `docs`: documentación del proyecto y contrato Swagger.
