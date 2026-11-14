"""Comunicación con el catálogo de películas de TMDB."""

import requests


BUSQUEDA_URL = "https://api.themoviedb.org/3/search/movie"
IMAGEN_BASE_URL = "https://image.tmdb.org/t/p/w500"
DETALLE_URL = "https://api.themoviedb.org/3/movie"

def buscar_peliculas(titulo, api_key, timeout=5):
    try:
        respuesta = requests.get(
            BUSQUEDA_URL,
            params={
                "api_key": api_key,
                "query": titulo,
                "language": "es-AR",
                "include_adult": "false",
            },
            timeout=timeout,
        )
        respuesta.raise_for_status()
        contenido = respuesta.json()
    except (requests.RequestException, ValueError):
        raise RuntimeError("No fue posible consultar TMDB.")

    if not isinstance(contenido, dict):
        raise RuntimeError("TMDB devolvió una respuesta inválida.")

    resultados = contenido.get("results")
    if not isinstance(resultados, list):
        raise RuntimeError("TMDB devolvió una respuesta inválida.")

    peliculas = []
    for resultado in resultados:
        if not isinstance(resultado, dict):
            continue
        id_externo = resultado.get("id")
        titulo_resultado = resultado.get("title")
        if (
            isinstance(id_externo, bool)
            or not isinstance(id_externo, int)
            or not isinstance(titulo_resultado, str)
            or not titulo_resultado
        ):
            continue

        poster_path = resultado.get("poster_path")
        if not isinstance(poster_path, str) or not poster_path:
            poster_path = None
        sinopsis = resultado.get("overview")
        if not isinstance(sinopsis, str) or not sinopsis:
            sinopsis = None
        peliculas.append(
            {
                "id_externo": id_externo,
                "titulo": titulo_resultado,
                "sinopsis": sinopsis,
                "poster_url": (
                    f"{IMAGEN_BASE_URL}{poster_path}" if poster_path else None
                ),
            }
        )

    return peliculas


def _clasificacion_argentina(datos):
    estrenos = datos.get("release_dates")
    if not isinstance(estrenos, dict):
        return ""

    paises = estrenos.get("results", [])
    if not isinstance(paises, list):
        return ""

    for pais in paises:
        if not isinstance(pais, dict) or pais.get("iso_3166_1") != "AR":
            continue

        fechas = pais.get("release_dates", [])
        if not isinstance(fechas, list):
            continue

        # Prioriza la clasificación del estreno en cines.
        for tipo in (3, 2, 1, 4, 5, 6):
            for estreno in fechas:
                if not isinstance(estreno, dict) or estreno.get("type") != tipo:
                    continue

                clasificacion = estreno.get("certification")
                if isinstance(clasificacion, str) and clasificacion.strip():
                    return clasificacion.strip()

    return ""


def obtener_pelicula(id_externo, api_key, timeout=5):
    try:
        respuesta = requests.get(
            f"{DETALLE_URL}/{id_externo}",
            params={
                "api_key": api_key,
                "language": "es-AR",
                "append_to_response": "release_dates",
            },
            timeout=timeout,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(datos, dict):
        return None

    titulo = datos.get("title")
    if not isinstance(titulo, str) or not titulo.strip():
        return None

    generos = datos.get("genres", [])
    if not isinstance(generos, list):
        generos = []

    nombres_generos = []
    for genero in generos:
        if not isinstance(genero, dict):
            continue

        nombre = genero.get("name")
        if isinstance(nombre, str) and nombre.strip():
            nombre = nombre.strip()
            if nombre not in nombres_generos:
                nombres_generos.append(nombre)

    duracion = datos.get("runtime")
    if type(duracion) is not int or duracion <= 0:
        duracion = None

    sinopsis = datos.get("overview")
    if not isinstance(sinopsis, str):
        sinopsis = ""

    poster = datos.get("poster_path")
    poster_url = ""
    if isinstance(poster, str) and poster.startswith("/"):
        poster_url = f"{IMAGEN_BASE_URL}{poster}"

    return {
        "id_externo": id_externo,
        "titulo": titulo.strip(),
        "sinopsis": sinopsis,
        "poster_url": poster_url,
        "duracion_minutos": duracion,
        "clasificacion": _clasificacion_argentina(datos),
        "genero": ", ".join(nombres_generos),
        "generos_tmdb": [
            genero["id"]
            for genero in generos
            if isinstance(genero, dict) and type(genero.get("id")) is int
        ],
    }