# Cine Paradiso API

Backend del sistema de venta de entradas de Cine Paradiso, desarrollado con
Python, Flask y MySQL. El Compose también construye e inicia el frontend Flask
ubicado en el directorio hermano `cine-paradiso-web`.

## Levantar el proyecto con Docker

### Requisitos

- Docker Engine o Docker Desktop.
- Docker Compose v2, disponible mediante el comando `docker compose`.

No es necesario instalar Python ni MySQL en la computadora. Los directorios
`cine_paradiso_api` y `cine-paradiso-web` deben conservarse uno junto al otro.

### Configuración inicial

1. Entrar al directorio del backend:

   ```bash
   cd cine_paradiso_api
   ```

2. Crear el archivo de configuración local:

   ```bash
   cp .env.example .env
   ```

3. Revisar `.env` y reemplazar, como mínimo, `SECRET_KEY`,
   `FRONTEND_SECRET_KEY`, `DB_PASSWORD` y `DB_ROOT_PASSWORD`. Los valores del
   ejemplo están pensados únicamente para desarrollo local y no deben usarse
   en producción.

   `MOVIES_API_KEY` es necesaria para los endpoints que consultan la API
   externa de películas. El resto del backend puede levantarse sin esa clave.

### Iniciar todo el proyecto

Construir la imagen e iniciar los servicios:

```bash
docker compose up --build
```

Para ejecutarlos en segundo plano:

```bash
docker compose up --build -d
```

Durante el primer inicio, MySQL crea la base de datos y ejecuta en orden los
archivos de `sql/`. Compose espera a que MySQL acepte conexiones antes de
iniciar la API, y espera a que la API esté saludable antes de iniciar el
frontend.

El frontend queda disponible en:

```text
http://localhost:8080
```

La API queda disponible en:

```text
http://localhost:5000
```

Se puede comprobar la conexión entre la API y MySQL consultando:

```bash
curl http://localhost:5000/cartelera
```

Como `02_datos_iniciales.sql` todavía no contiene registros, la respuesta
inicial esperada es una cartelera vacía.

Los puertos se pueden cambiar en `.env` mediante `FRONTEND_PORT` y `API_PORT`.
La comunicación entre contenedores no depende de esos puertos publicados: el
frontend accede a la API mediante el nombre interno `api`.

### Estado y logs

Consultar el estado de los contenedores:

```bash
docker compose ps
```

Seguir los logs de todos los servicios:

```bash
docker compose logs -f
```

O consultar un servicio en particular:

```bash
docker compose logs -f api
docker compose logs -f db
docker compose logs -f frontend
```

### Ejecutar las pruebas

Con los servicios iniciados:

```bash
docker compose exec api pytest
```

También se pueden ejecutar en un contenedor temporal sin iniciar la API:

```bash
docker compose run --rm --no-deps api pytest
```

### Detener los servicios

Detener y eliminar los contenedores conservando la base de datos:

```bash
docker compose down
```

Los datos de MySQL se guardan en un volumen de Docker y permanecen disponibles
para el próximo inicio.

Para eliminar también la base de datos y recrearla desde los scripts SQL:

```bash
docker compose down -v
docker compose up --build
```

`docker compose down -v` elimina todos los datos locales de MySQL. Los scripts
de `sql/` solamente se ejecutan automáticamente cuando el volumen se crea por
primera vez.

### Reconstruir después de realizar cambios

Los cambios en el código o en `requirements.txt` requieren reconstruir la
imagen:

```bash
docker compose up --build -d
```

### Solución de problemas

- Si el puerto 5000 está ocupado, cambiar `API_PORT` en `.env`.
- Si el puerto 8080 está ocupado, cambiar `FRONTEND_PORT` en `.env`.
- Si la API no inicia, revisar `docker compose logs api` y
  `docker compose logs db`.
- Si el frontend no inicia, revisar `docker compose logs frontend`.
- Si se modificó el esquema SQL pero el volumen ya existía, recrear la base con
  `docker compose down -v`. Esto elimina los datos existentes.
- Si se cambian `DB_USER`, `DB_PASSWORD` o `DB_ROOT_PASSWORD` después del primer
  inicio, también es necesario recrear el volumen para que MySQL aplique las
  nuevas credenciales.
- MySQL no publica el puerto 3306 en la computadora. Para abrir su consola usar:

  ```bash
  docker compose exec db mysql -u root -p
  ```

## Ejecución local sin Docker

1. Crear y activar un entorno virtual de Python.
2. Instalar y configurar MySQL 8.0 o superior.
3. Ejecutar los archivos de `sql/` en orden.
4. Instalar las dependencias con `pip install -r requirements.txt`.
5. Copiar `.env.example` como `.env` y completar la configuración local. En
   este modo, `DB_HOST=127.0.0.1` apunta al MySQL instalado localmente.
6. Ejecutar la aplicación con `python run.py`.

El archivo `.env` contiene datos locales y no debe subirse al repositorio.

## Servicios de Docker

- `api`: aplicación Flask publicada en el puerto configurado por `API_PORT`.
- `db`: MySQL 8.0, accesible para la API mediante el nombre interno `db`.
- `frontend`: aplicación web Flask publicada en el puerto configurado por
  `FRONTEND_PORT` y conectada internamente con `http://api:5000`.
- `mysql_data`: volumen persistente con los datos de MySQL.

## Organización

- `app/routes`: endpoints HTTP definidos en el contrato Swagger.
- `app/validators`: validación de los datos recibidos.
- `app/services`: reglas de negocio.
- `app/repositories`: consultas SQL parametrizadas contra MySQL.
- `app/integrations`: API de películas, correo electrónico y códigos QR.
- `sql`: creación de tablas y datos iniciales.
- `tests`: pruebas automatizadas.
- `docs`: documentación del proyecto y contrato Swagger.

## Respuestas de error

Todos los errores se devuelven como JSON con el mismo contrato:

```json
{
  "codigo": "DATOS_INVALIDOS",
  "mensaje": "Los datos enviados son inválidos",
  "detalles": [
    {
      "campo": "general",
      "mensaje": "Revise el formato y los datos de la solicitud."
    }
  ]
}
```

Los estados HTTP conservan su semántica: `400` para datos inválidos, `401`
para autenticación ausente o inválida, `403` para permisos insuficientes,
`404` para recursos inexistentes y `409` para conflictos con el estado o la
disponibilidad de un recurso. El campo `codigo` permite distinguir el motivo
específico, por ejemplo un email duplicado, una butaca no disponible o una
entrada cancelada.
