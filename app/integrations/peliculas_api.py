"""Comunicación con el catálogo de películas de TMDB."""

import requests


BUSQUEDA_URL = "https://api.themoviedb.org/3/search/movie"
IMAGEN_BASE_URL = "https://image.tmdb.org/t/p/w500"

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

