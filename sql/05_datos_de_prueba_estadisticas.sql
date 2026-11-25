-- Cine Paradiso - datos de prueba para la pestaña ESTADÍSTICAS
-- MySQL 8.0+
-- Usa las películas que ya existen y también todas las
-- películas importadas desde el catálogo externo.
-- Crea una sala "Sala Estadísticas" en cada local con
-- sus butacas, para no chocar con las funciones reales del cine.
-- Crea funciones pasadas y futuras (dos canceladas), compras
-- confirmadas y canceladas (con motivo), butacas vendidas y entradas.
-- Las fechas son relativas a hoy, así los filtros "Últimos 7 días" y
-- "Últimos 30 días" siempre muestran datos.
--
-- Se puede ejecutar varias veces: primero borra todo lo que haya cargado
-- antes. Si importaste películas nuevas, hay que ejecutarlo nuevamente para
-- que tengan funciones.
-- =====================================================================

SET NAMES utf8mb4;

USE cine_paradiso;

START TRANSACTION;


-- Limpieza de una carga anterior

DELETE e
FROM entradas AS e
INNER JOIN compras AS c ON c.id = e.compra_id
INNER JOIN funciones AS f ON f.id = c.funcion_id
WHERE f.sala_id BETWEEN 9001 AND 9003;

DELETE c
FROM compras AS c
INNER JOIN funciones AS f ON f.id = c.funcion_id
WHERE f.sala_id BETWEEN 9001 AND 9003;

DELETE bf
FROM butacas_funcion AS bf
INNER JOIN funciones AS f ON f.id = bf.funcion_id
WHERE f.sala_id BETWEEN 9001 AND 9003;

DELETE FROM funciones WHERE sala_id BETWEEN 9001 AND 9003;
DELETE FROM butacas   WHERE sala_id BETWEEN 9001 AND 9003;
DELETE FROM salas     WHERE id BETWEEN 9001 AND 9003;


-- Salas de prueba (una por local) con distintas capacidades

INSERT INTO salas (id, local_id, nombre, filas, butacas_por_fila, activa)
VALUES
    (9001, 1, 'Sala Estadísticas',  8, 10, TRUE),   --  80 butacas
    (9002, 2, 'Sala Estadísticas',  6,  8, TRUE),   --  48 butacas
    (9003, 3, 'Sala Estadísticas', 10, 12, TRUE);   -- 120 butacas


INSERT INTO butacas (sala_id, fila, numero, activa)
WITH RECURSIVE numeros AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM numeros WHERE n < 20
)
SELECT s.id, CHAR(64 + filas.n), columnas.n, TRUE
FROM salas AS s
INNER JOIN numeros AS filas ON filas.n <= s.filas
INNER JOIN numeros AS columnas ON columnas.n <= s.butacas_por_fila
WHERE s.id BETWEEN 9001 AND 9003;


-- Funciones de las películas del sistema
INSERT INTO funciones (id, pelicula_id, sala_id, fecha_hora, precio, estado, formato, idioma)
VALUES
    (9001, 1, 9003, TIMESTAMP(CURDATE() - INTERVAL  6 DAY, '19:30:00'), 6500, 'programada', '2D',      'Castellano'),
    (9002, 1, 9001, TIMESTAMP(CURDATE() - INTERVAL  3 DAY, '22:00:00'), 7200, 'programada', '3D',      'Subtitulada'),
    (9003, 2, 9002, TIMESTAMP(CURDATE() - INTERVAL  5 DAY, '16:00:00'), 6000, 'programada', '2D',      'Castellano'),
    (9004, 2, 9003, TIMESTAMP(CURDATE() - INTERVAL  2 DAY, '20:00:00'), 6000, 'programada', '2D',      'Castellano'),
    (9005, 3, 9001, TIMESTAMP(CURDATE() - INTERVAL  4 DAY, '13:00:00'), 7000, 'programada', '2D',      'Subtitulada'),
    (9006, 3, 9003, TIMESTAMP(CURDATE() - INTERVAL  1 DAY, '21:30:00'), 7000, 'programada', '2D',      'Subtitulada'),
    (9007, 4, 9002, TIMESTAMP(CURDATE() - INTERVAL  1 DAY, '23:00:00'), 6200, 'programada', '2D',      'Castellano'),
    (9008, 4, 9001, TIMESTAMP(CURDATE() - INTERVAL  3 DAY, '10:30:00'), 6200, 'programada', '2D',      'Castellano'),
    (9009, 2, 9001, TIMESTAMP(CURDATE(),                   '18:00:00'), 6000, 'programada', '4D',      'Castellano'),
    (9010, 1, 9003, TIMESTAMP(CURDATE() + INTERVAL  1 DAY, '20:30:00'), 7200, 'programada', '3D',      'Subtitulada'),
    (9011, 3, 9002, TIMESTAMP(CURDATE() - INTERVAL  4 DAY, '19:00:00'), 7000, 'cancelada',  '2D',      'Subtitulada'),
    (9012, 4, 9003, TIMESTAMP(CURDATE() + INTERVAL  2 DAY, '17:00:00'), 6200, 'cancelada',  'Confort', 'Castellano'),
    (9013, 2, 9003, TIMESTAMP(CURDATE() - INTERVAL 20 DAY, '19:00:00'), 6000, 'programada', '2D',      'Castellano'),
    (9014, 3, 9001, TIMESTAMP(CURDATE() - INTERVAL 25 DAY, '15:00:00'), 7000, 'programada', '2D',      'Subtitulada');


-- Funciones de las películas IMPORTADAS del catálogo externo
INSERT INTO funciones (pelicula_id, sala_id, fecha_hora, precio, estado, formato, idioma)
SELECT
    importadas.id,
    salas_horarios.sala_id,
    TIMESTAMP(
        CURDATE() - INTERVAL (importadas.orden + salas_horarios.dias_extra) DAY,
        salas_horarios.hora
    ),
    6500,
    'programada',
    '2D',
    'Subtitulada'
FROM (
    SELECT p.id, ROW_NUMBER() OVER (ORDER BY p.id) AS orden
    FROM peliculas AS p
    WHERE p.id_externo IS NOT NULL
      AND p.activa = TRUE
) AS importadas
CROSS JOIN (
    SELECT 9003 AS sala_id, '15:45:00' AS hora, 0 AS dias_extra
    UNION ALL
    SELECT 9001, '23:15:00', 7
) AS salas_horarios;

-- Cuántas entradas vende y cuántas compras se cancelan en cada función

DROP TEMPORARY TABLE IF EXISTS seed_objetivos;
CREATE TEMPORARY TABLE seed_objetivos (
    funcion_id INT UNSIGNED PRIMARY KEY,
    vendidas   INT NOT NULL,
    canceladas INT NOT NULL
);

INSERT INTO seed_objetivos (funcion_id, vendidas, canceladas) VALUES
    (9001,  96, 2),   
    (9002,  70, 1),   
    (9003,  18, 0),   
    (9004, 110, 1),   
    (9005,  20, 0),   
    (9006,  84, 3),   
    (9007,  30, 0),   
    (9008,  12, 0),   
    (9009,  41, 1),   
    (9010,  40, 0),   
    (9011,   0, 3),   
    (9012,   0, 0),   
    (9013, 100, 0),   
    (9014,  50, 1);   

-- Películas importadas: entre 20 y 69 entradas por función (sin pasarse
-- de la capacidad) y a veces una compra cancelada.

INSERT INTO seed_objetivos (funcion_id, vendidas, canceladas)
SELECT
    f.id,
    LEAST(20 + MOD(f.pelicula_id * 37 + f.sala_id, 50), s.filas * s.butacas_por_fila - 2),
    MOD(f.pelicula_id + f.sala_id, 2)
FROM funciones AS f
INNER JOIN salas AS s ON s.id = f.sala_id
WHERE f.sala_id BETWEEN 9001 AND 9003
  AND f.id NOT BETWEEN 9001 AND 9014;


-- Compras: total_entradas es un MONTO (cantidad x precio), no una cantidad.
-- Las compras confirmadas son de hasta 4 entradas.

INSERT INTO compras (
    usuario_id, funcion_id, fecha_hora, estado, medio_pago,
    total_entradas, total_servicios, total, motivo_cancelacion
)
WITH RECURSIVE numeros AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM numeros WHERE n < 40
)
SELECT
    1,
    o.funcion_id,
    LEAST(NOW(), f.fecha_hora - INTERVAL (1 + MOD(numeros.n, 5)) DAY),
    'confirmada',
    'tarjeta',
    LEAST(4, o.vendidas - (numeros.n - 1) * 4) * f.precio,
    0,
    LEAST(4, o.vendidas - (numeros.n - 1) * 4) * f.precio,
    NULL
FROM seed_objetivos AS o
INNER JOIN funciones AS f ON f.id = o.funcion_id
INNER JOIN numeros ON numeros.n <= CEIL(o.vendidas / 4);

-- Compras canceladas: 2 entradas cada una, con motivo.
INSERT INTO compras (
    usuario_id, funcion_id, fecha_hora, estado, medio_pago,
    total_entradas, total_servicios, total, motivo_cancelacion
)
WITH RECURSIVE numeros AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM numeros WHERE n < 5
)
SELECT
    1,
    o.funcion_id,
    LEAST(NOW(), f.fecha_hora - INTERVAL (2 + numeros.n) DAY),
    'cancelada',
    'tarjeta',
    2 * f.precio,
    0,
    2 * f.precio,
    CASE
        WHEN f.estado = 'cancelada' THEN 'La función fue cancelada por el cine.'
        WHEN MOD(numeros.n + f.id, 3) = 0 THEN 'El cliente no podía asistir.'
        WHEN MOD(numeros.n + f.id, 3) = 1 THEN 'Eligió butacas equivocadas.'
        ELSE 'Cambio de horario solicitado por el cliente.'
    END
FROM seed_objetivos AS o
INNER JOIN funciones AS f ON f.id = o.funcion_id
INNER JOIN numeros ON numeros.n <= o.canceladas;


-- Una "entrada pendiente" por cada butaca comprada, numeradas por
-- función (1, 2, 3...) para asignarles butacas distintas.

DROP TEMPORARY TABLE IF EXISTS seed_entradas;
CREATE TEMPORARY TABLE seed_entradas (
    compra_id   INT UNSIGNED NOT NULL,
    funcion_id  INT UNSIGNED NOT NULL,
    sala_id     INT UNSIGNED NOT NULL,
    posicion    INT NOT NULL,
    PRIMARY KEY (funcion_id, posicion)
);

INSERT INTO seed_entradas (compra_id, funcion_id, sala_id, posicion)
WITH RECURSIVE numeros AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM numeros WHERE n < 4
)
SELECT
    c.id,
    c.funcion_id,
    f.sala_id,
    ROW_NUMBER() OVER (PARTITION BY c.funcion_id ORDER BY c.id, numeros.n)
FROM compras AS c
INNER JOIN funciones AS f ON f.id = c.funcion_id
INNER JOIN numeros ON numeros.n <= ROUND(c.total_entradas / f.precio)
WHERE f.sala_id BETWEEN 9001 AND 9003;

-- Butacas de cada sala numeradas en orden (A1, A2, ... B1, ...).
DROP TEMPORARY TABLE IF EXISTS seed_butacas;
CREATE TEMPORARY TABLE seed_butacas (
    sala_id   INT UNSIGNED NOT NULL,
    posicion  INT NOT NULL,
    butaca_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (sala_id, posicion)
);

INSERT INTO seed_butacas (sala_id, posicion, butaca_id)
SELECT
    b.sala_id,
    ROW_NUMBER() OVER (PARTITION BY b.sala_id ORDER BY b.fila, b.numero),
    b.id
FROM butacas AS b
WHERE b.sala_id BETWEEN 9001 AND 9003;


-- Butacas de cada función: 'vendida' si la compra está confirmada, 'disponible' si la compra se canceló (la butaca se liberó).

INSERT INTO butacas_funcion (funcion_id, butaca_id, estado, reserva_hasta, reserva_id)
SELECT
    se.funcion_id,
    sb.butaca_id,
    CASE WHEN c.estado = 'confirmada' THEN 'vendida' ELSE 'disponible' END,
    NULL,
    NULL
FROM seed_entradas AS se
INNER JOIN seed_butacas AS sb
    ON sb.sala_id = se.sala_id
   AND sb.posicion = se.posicion
INNER JOIN compras AS c ON c.id = se.compra_id;


-- Entradas: Funciones pasadas: 'utilizada' (1 de cada 5 quedó 'vigente': no fue).
-- Funciones futuras: 'vigente'. Compras canceladas: 'cancelada'.

INSERT INTO entradas (
    compra_id, butaca_funcion_id, precio, codigo_qr, estado,
    fecha_hora_validacion, fecha_hora_cancelacion
)
SELECT
    c.id,
    bf.id,
    f.precio,
    CONCAT('QRCINE-EST-', f.id, '-', se.posicion),
    CASE
        WHEN c.estado = 'cancelada' THEN 'cancelada'
        WHEN f.fecha_hora < NOW() AND MOD(se.posicion, 5) <> 0 THEN 'utilizada'
        ELSE 'vigente'
    END,
    CASE
        WHEN c.estado = 'confirmada' AND f.fecha_hora < NOW() AND MOD(se.posicion, 5) <> 0
        THEN f.fecha_hora - INTERVAL 10 MINUTE
    END,
    CASE
        WHEN c.estado = 'cancelada' THEN LEAST(NOW(), c.fecha_hora + INTERVAL 1 DAY)
    END
FROM seed_entradas AS se
INNER JOIN compras AS c ON c.id = se.compra_id
INNER JOIN funciones AS f ON f.id = se.funcion_id
INNER JOIN seed_butacas AS sb
    ON sb.sala_id = se.sala_id
   AND sb.posicion = se.posicion
INNER JOIN butacas_funcion AS bf
    ON bf.funcion_id = se.funcion_id
   AND bf.butaca_id = sb.butaca_id;

DROP TEMPORARY TABLE IF EXISTS seed_objetivos;
DROP TEMPORARY TABLE IF EXISTS seed_entradas;
DROP TEMPORARY TABLE IF EXISTS seed_butacas;

COMMIT;


-- Control rápido
-- Películas del sistema: 671 entradas vendidas y 12 compras canceladas.
-- Películas importadas: depende de cuántas tengas cargadas.

SELECT
    CASE WHEN p.id_externo IS NULL THEN 'Películas del sistema' ELSE 'Películas importadas' END AS origen,
    COUNT(DISTINCT p.id) AS peliculas,
    COUNT(DISTINCT f.id) AS funciones,
    COUNT(DISTINCT CASE WHEN c.estado = 'confirmada' THEN e.id END) AS entradas_vendidas,
    COUNT(DISTINCT CASE WHEN c.estado = 'cancelada' THEN c.id END) AS compras_canceladas
FROM funciones AS f
INNER JOIN peliculas AS p ON p.id = f.pelicula_id
LEFT JOIN compras AS c ON c.funcion_id = f.id
LEFT JOIN entradas AS e ON e.compra_id = c.id
WHERE f.sala_id BETWEEN 9001 AND 9003
GROUP BY origen;
