-- Cine Paradiso - categorías y filtros de películas
-- MySQL 8.0+
-- Una película puede pertenecer a varias categorías.
-- Cada función tiene su propio formato e idioma.
-- Los valores permitidos de formato e idioma se validan en Flask.
-- Ejecutar una sola vez después del esquema inicial.

SET NAMES utf8mb4;

USE cine_paradiso;

-- Categorías disponibles para clasificar y filtrar películas.
CREATE TABLE IF NOT EXISTS categorias (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    UNIQUE KEY uq_categorias_nombre (nombre)
);

-- Relación entre películas y categorías.
CREATE TABLE IF NOT EXISTS peliculas_categorias (
    pelicula_id INT UNSIGNED NOT NULL,
    categoria_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (pelicula_id, categoria_id),
    CONSTRAINT fk_peliculas_categorias_pelicula
        FOREIGN KEY (pelicula_id) REFERENCES peliculas(id),
    CONSTRAINT fk_peliculas_categorias_categoria
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

-- Las funciones existentes quedan sin formato e idioma hasta completarlos.
ALTER TABLE funciones
    ADD COLUMN formato VARCHAR(20) NULL,
    ADD COLUMN idioma VARCHAR(20) NULL;

-- Agrega las categorías iniciales que todavía no existen.
INSERT INTO categorias (nombre)
SELECT opciones.nombre
FROM (
    SELECT 1 AS orden, 'Cine de Culto' AS nombre
    UNION ALL SELECT 2, 'Drama'
    UNION ALL SELECT 3, 'Acción'
    UNION ALL SELECT 4, 'Aventura'
    UNION ALL SELECT 5, 'Ciencia Ficción'
    UNION ALL SELECT 6, 'Terror / Horror'
    UNION ALL SELECT 7, 'Comedia'
    UNION ALL SELECT 8, 'Suspenso / Thriller'
    UNION ALL SELECT 9, 'Animación / Infantil'
    UNION ALL SELECT 10, 'Documental'
    UNION ALL SELECT 11, 'Romance'
    UNION ALL SELECT 12, 'Clásicos'
) AS opciones
WHERE NOT EXISTS (
    SELECT 1
    FROM categorias
    WHERE categorias.nombre = opciones.nombre
)
ORDER BY opciones.orden;
