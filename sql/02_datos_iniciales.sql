-- Cine Paradiso - datos iniciales para desarrollo local
-- Este script puede ejecutarse más de una vez sin duplicar los registros.

USE cine_paradiso;

START TRANSACTION;

-- Locales disponibles para la cartelera.
INSERT INTO locales (id, nombre, direccion, activa)
VALUES
    (1, 'Cine Paradiso Centro', 'Av. Corrientes 1234, CABA', TRUE),
    (2, 'Cine Paradiso Norte', 'Av. Cabildo 2345, CABA', TRUE),
    (3, 'Cine Paradiso Puerto', 'Av. Alicia Moreau de Justo 850, CABA', TRUE)
ON DUPLICATE KEY UPDATE
    nombre = VALUES(nombre),
    direccion = VALUES(direccion),
    activa = VALUES(activa);

-- Una sala de seis filas y ocho butacas para cada local.
INSERT INTO salas (id, local_id, nombre, filas, butacas_por_fila, activa)
VALUES
    (1, 1, 'Sala 1', 6, 8, TRUE),
    (2, 2, 'Sala 1', 6, 8, TRUE),
    (3, 3, 'Sala 1', 6, 8, TRUE)
ON DUPLICATE KEY UPDATE
    local_id = VALUES(local_id),
    nombre = VALUES(nombre),
    filas = VALUES(filas),
    butacas_por_fila = VALUES(butacas_por_fila),
    activa = VALUES(activa);

-- Genera las 48 butacas físicas de cada sala (filas A-F, números 1-8).
INSERT INTO butacas (sala_id, fila, numero, activa)
SELECT
    salas_demo.id,
    filas_demo.fila,
    numeros_demo.numero,
    TRUE
FROM (
    SELECT 1 AS id
    UNION ALL SELECT 2
    UNION ALL SELECT 3
) AS salas_demo
CROSS JOIN (
    SELECT 'A' AS fila
    UNION ALL SELECT 'B'
    UNION ALL SELECT 'C'
    UNION ALL SELECT 'D'
    UNION ALL SELECT 'E'
    UNION ALL SELECT 'F'
) AS filas_demo
CROSS JOIN (
    SELECT 1 AS numero
    UNION ALL SELECT 2
    UNION ALL SELECT 3
    UNION ALL SELECT 4
    UNION ALL SELECT 5
    UNION ALL SELECT 6
    UNION ALL SELECT 7
    UNION ALL SELECT 8
) AS numeros_demo
WHERE TRUE
ON DUPLICATE KEY UPDATE activa = TRUE;

-- Películas locales. Más adelante el administrador podrá importar otras
-- películas desde TMDB mediante el backend.
INSERT INTO peliculas (
    id, id_externo, titulo, sinopsis, poster_url, duracion_minutos,
    clasificacion, genero, disponible_desde, disponible_hasta, activa
)
VALUES
    (1, NULL, 'Horizonte final',
     'Una tripulación emprende el último viaje hacia una estación perdida.',
     'https://placehold.co/500x750/0b1630/ffffff?text=Horizonte+final',
     128, '+13', 'Ciencia ficción',
     DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 180 DAY), TRUE),
    (2, NULL, 'La última función',
     'El cierre de un antiguo cine reúne a sus trabajadores y espectadores.',
     'https://placehold.co/500x750/742746/ffffff?text=La+ultima+funcion',
     112, 'ATP', 'Drama',
     DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 180 DAY), TRUE),
    (3, NULL, 'Código nocturno',
     'Una analista descubre un mensaje oculto que conecta varias desapariciones.',
     'https://placehold.co/500x750/103b4a/ffffff?text=Codigo+nocturno',
     106, '+16', 'Suspenso',
     DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 180 DAY), TRUE),
    (4, NULL, 'Un verano contigo',
     'Dos amigos regresan al pueblo donde crecieron y recuperan viejas promesas.',
     'https://placehold.co/500x750/e99648/ffffff?text=Un+verano+contigo',
     99, 'ATP', 'Romance',
     DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_ADD(NOW(), INTERVAL 180 DAY), TRUE)
ON DUPLICATE KEY UPDATE
    titulo = VALUES(titulo),
    sinopsis = VALUES(sinopsis),
    poster_url = VALUES(poster_url),
    duracion_minutos = VALUES(duracion_minutos),
    clasificacion = VALUES(clasificacion),
    genero = VALUES(genero),
    disponible_desde = VALUES(disponible_desde),
    disponible_hasta = VALUES(disponible_hasta),
    activa = VALUES(activa);

-- Las fechas se calculan al ejecutar el script para que siempre existan
-- funciones futuras durante las pruebas locales.
INSERT INTO funciones (id, pelicula_id, sala_id, fecha_hora, precio, estado)
VALUES
    (101, 1, 1, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '18:30:00'), 6500, 'programada'),
    (102, 1, 1, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 1 DAY), '21:15:00'), 7200, 'programada'),
    (103, 2, 2, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '17:45:00'), 6000, 'programada'),
    (104, 3, 3, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 2 DAY), '20:30:00'), 7000, 'programada'),
    (105, 4, 1, TIMESTAMP(DATE_ADD(CURDATE(), INTERVAL 3 DAY), '19:00:00'), 6200, 'programada')
ON DUPLICATE KEY UPDATE
    pelicula_id = VALUES(pelicula_id),
    sala_id = VALUES(sala_id),
    fecha_hora = VALUES(fecha_hora),
    precio = VALUES(precio),
    estado = VALUES(estado);

-- Productos disponibles para el paso de Candy.
INSERT INTO servicios (id, nombre, descripcion, precio, activo)
VALUES
    (1, 'Combo Paradiso', 'Pochoclos grandes y dos gaseosas medianas.', 14800, TRUE),
    (2, 'Combo Dúo', 'Pochoclos medianos y dos gaseosas chicas.', 11200, TRUE),
    (3, 'Pochoclos clásicos', 'Pochoclos acaramelados tamaño grande.', 6800, TRUE),
    (4, 'Gaseosa mediana', 'Vaso de 500 ml, sabor a elección.', 4200, TRUE),
    (5, 'Nachos con cheddar', 'Nachos crocantes con salsa de cheddar.', 5900, TRUE),
    (6, 'Chocolate', 'Chocolate con leche de 100 gramos.', 3500, TRUE),
    (7, 'Café con leche', 'Café suave con leche espumada.', 3900, TRUE),
    (8, 'Helado individual', 'Pote individual, sabor a elección.', 4700, TRUE)
ON DUPLICATE KEY UPDATE
    nombre = VALUES(nombre),
    descripcion = VALUES(descripcion),
    precio = VALUES(precio),
    activo = VALUES(activo);

-- Usuarios locales para probar autenticación y permisos.
-- Cliente: cliente@cineparadiso.local / Cliente123!
-- Administrador: admin@cineparadiso.local / Admin123!
INSERT INTO usuarios (id, nombre, email, password_hash, rol, activo)
VALUES
    (1, 'Cliente Demo', 'cliente@cineparadiso.local',
     'pbkdf2:sha256:600000$cinecliente2026$a9f36eb24e051e1a637c174df361ff7413212624fdb9258b8a8c2a8a54b5a4c5',
     'cliente', TRUE),
    (2, 'Administrador Demo', 'admin@cineparadiso.local',
     'pbkdf2:sha256:600000$cineadmin2026$971eda2825ae503c5951385428a098ed50a3d8756f797edc16089ce6fe6331e8',
     'administrador', TRUE)
ON DUPLICATE KEY UPDATE
    nombre = VALUES(nombre),
    email = VALUES(email),
    password_hash = VALUES(password_hash),
    rol = VALUES(rol),
    activo = VALUES(activo);

-- Algunas butacas ocupadas permiten comprobar visualmente los estados.
INSERT INTO butacas_funcion (funcion_id, butaca_id, estado, reserva_hasta)
SELECT 101, b.id, 'ocupada', NULL
FROM butacas AS b
WHERE b.sala_id = 1
  AND ((b.fila = 'A' AND b.numero = 3)
       OR (b.fila = 'B' AND b.numero = 5)
       OR (b.fila = 'D' AND b.numero = 7))
ON DUPLICATE KEY UPDATE
    estado = 'ocupada',
    reserva_hasta = NULL;

COMMIT;

