-- Reservas temporales de butacas y pagos simulados
-- MySQL 8.0+ / InnoDB
--
-- Esta migracion se ejecuta una sola vez despues de 01_crear_tablas.sql.
-- Todos los timestamps de este flujo se escriben con UTC_TIMESTAMP().

USE cine_paradiso;

CREATE TABLE reservas (
    id CHAR(36) PRIMARY KEY,
    usuario_id INT UNSIGNED NOT NULL,
    funcion_id INT UNSIGNED NOT NULL,
    estado VARCHAR(30) NOT NULL,
    creada_en DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP()),
    expira_en DATETIME NOT NULL,
    idempotencia_pago VARCHAR(128) NULL,
    compra_id INT UNSIGNED NULL,
    actualizada_en DATETIME NOT NULL DEFAULT (UTC_TIMESTAMP()),
    CONSTRAINT fk_reservas_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    CONSTRAINT fk_reservas_funcion
        FOREIGN KEY (funcion_id) REFERENCES funciones(id),
    CONSTRAINT fk_reservas_compra
        FOREIGN KEY (compra_id) REFERENCES compras(id),
    UNIQUE KEY uq_reservas_compra (compra_id),
    KEY ix_reservas_usuario_funcion_estado
        (usuario_id, funcion_id, estado),
    KEY ix_reservas_estado_expiracion (estado, expira_en)
) ENGINE=InnoDB;

ALTER TABLE butacas_funcion
    ADD COLUMN reserva_id CHAR(36) NULL AFTER reserva_hasta,
    ADD CONSTRAINT fk_butacas_funcion_reserva
        FOREIGN KEY (reserva_id) REFERENCES reservas(id),
    ADD KEY ix_butacas_funcion_estado_expiracion
        (estado, reserva_hasta),
    ADD KEY ix_butacas_funcion_reserva (reserva_id);

ALTER TABLE compras
    ADD COLUMN reserva_id CHAR(36) NULL AFTER funcion_id,
    ADD CONSTRAINT fk_compras_reserva
        FOREIGN KEY (reserva_id) REFERENCES reservas(id),
    ADD UNIQUE KEY uq_compras_reserva (reserva_id);

-- Permite una sola entrada activa por butaca/funcion, pero deja volver a
-- venderla si una compra anterior fue cancelada.
ALTER TABLE entradas
    ADD COLUMN butaca_funcion_vendida_id INT UNSIGNED
        GENERATED ALWAYS AS (
            CASE
                WHEN estado IN ('emitida', 'vigente', 'utilizada')
                THEN butaca_funcion_id
                ELSE NULL
            END
        ) STORED,
    ADD UNIQUE KEY uq_entradas_butaca_funcion_vendida
        (butaca_funcion_vendida_id);

-- Normaliza ventas existentes al vocabulario nuevo sin perderlas.
UPDATE butacas_funcion
SET estado = 'vendida',
    reserva_hasta = NULL,
    reserva_id = NULL
WHERE estado = 'ocupada';

-- Las reservas historicas sin vencimiento no tienen propietario verificable;
-- se liberan para no dejar bloqueos permanentes despues de la migracion.
UPDATE butacas_funcion
SET estado = 'disponible',
    reserva_hasta = NULL,
    reserva_id = NULL
WHERE estado = 'reservada'
  AND reserva_hasta IS NULL;
