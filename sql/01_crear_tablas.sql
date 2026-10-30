-- Cine Paradiso - esquema inicial de base de datos
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS cine_paradiso
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE cine_paradiso;

CREATE TABLE IF NOT EXISTS locales (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE KEY uq_locales_nombre (nombre)
);

CREATE TABLE IF NOT EXISTS salas (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    local_id INT UNSIGNED NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    filas INT UNSIGNED NOT NULL,
    butacas_por_fila INT UNSIGNED NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_salas_filas CHECK (filas > 0),
    CONSTRAINT chk_salas_butacas_por_fila CHECK (butacas_por_fila > 0),
    CONSTRAINT fk_salas_local
        FOREIGN KEY (local_id) REFERENCES locales(id),
    UNIQUE KEY uq_salas_local_nombre (local_id, nombre)
);

CREATE TABLE IF NOT EXISTS butacas (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sala_id INT UNSIGNED NOT NULL,
    fila VARCHAR(3) NOT NULL,
    numero INT UNSIGNED NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_butacas_numero CHECK (numero > 0),
    CONSTRAINT fk_butacas_sala
        FOREIGN KEY (sala_id) REFERENCES salas(id),
    UNIQUE KEY uq_butacas_sala_fila_numero (sala_id, fila, numero)
);

CREATE TABLE IF NOT EXISTS peliculas (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    id_externo INT UNSIGNED NULL,
    titulo VARCHAR(200) NOT NULL,
    sinopsis TEXT NOT NULL,
    poster_url VARCHAR(500) NOT NULL,
    duracion_minutos INT UNSIGNED NOT NULL,
    clasificacion VARCHAR(20) NOT NULL,
    genero VARCHAR(100) NOT NULL,
    disponible_desde DATETIME NULL,
    disponible_hasta DATETIME NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_peliculas_duracion CHECK (duracion_minutos > 0),
    CONSTRAINT chk_peliculas_disponibilidad CHECK (
        disponible_desde IS NULL
        OR disponible_hasta IS NULL
        OR disponible_desde < disponible_hasta
    ),
    UNIQUE KEY uq_peliculas_id_externo (id_externo)
);

CREATE TABLE IF NOT EXISTS funciones (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    pelicula_id INT UNSIGNED NOT NULL,
    sala_id INT UNSIGNED NOT NULL,
    fecha_hora DATETIME NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    estado ENUM('programada', 'cancelada', 'finalizada') NOT NULL DEFAULT 'programada',
    CONSTRAINT chk_funciones_precio CHECK (precio >= 0),
    CONSTRAINT fk_funciones_pelicula
        FOREIGN KEY (pelicula_id) REFERENCES peliculas(id),
    CONSTRAINT fk_funciones_sala
        FOREIGN KEY (sala_id) REFERENCES salas(id),
    UNIQUE KEY uq_funciones_sala_fecha_hora (sala_id, fecha_hora)
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('cliente', 'administrador') NOT NULL DEFAULT 'cliente',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_usuarios_email (email)
);

CREATE TABLE IF NOT EXISTS servicios (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(500) NULL,
    precio DECIMAL(10, 2) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_servicios_precio CHECK (precio >= 0),
    UNIQUE KEY uq_servicios_nombre (nombre)
);

CREATE TABLE IF NOT EXISTS butacas_funcion (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    funcion_id INT UNSIGNED NOT NULL,
    butaca_id INT UNSIGNED NOT NULL,
    estado ENUM('disponible', 'reservada', 'ocupada') NOT NULL DEFAULT 'disponible',
    reserva_hasta DATETIME NULL,
    CONSTRAINT fk_butacas_funcion_funcion
        FOREIGN KEY (funcion_id) REFERENCES funciones(id),
    CONSTRAINT fk_butacas_funcion_butaca
        FOREIGN KEY (butaca_id) REFERENCES butacas(id),
    UNIQUE KEY uq_butacas_funcion (funcion_id, butaca_id)
);

CREATE TABLE IF NOT EXISTS compras (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT UNSIGNED NOT NULL,
    funcion_id INT UNSIGNED NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('confirmada', 'cancelada') NOT NULL DEFAULT 'confirmada',
    total DECIMAL(10, 2) NOT NULL,
    CONSTRAINT chk_compras_total CHECK (total >= 0),
    CONSTRAINT fk_compras_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    CONSTRAINT fk_compras_funcion
        FOREIGN KEY (funcion_id) REFERENCES funciones(id)
);

CREATE TABLE IF NOT EXISTS entradas (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    compra_id INT UNSIGNED NOT NULL,
    butaca_funcion_id INT UNSIGNED NOT NULL,
    precio DECIMAL(10, 2) NOT NULL,
    codigo_qr VARCHAR(255) NOT NULL,
    estado ENUM('emitida', 'utilizada', 'cancelada') NOT NULL DEFAULT 'emitida',
    fecha_hora_validacion DATETIME NULL,
    fecha_hora_cancelacion DATETIME NULL,
    CONSTRAINT chk_entradas_precio CHECK (precio >= 0),
    CONSTRAINT fk_entradas_compra
        FOREIGN KEY (compra_id) REFERENCES compras(id),
    CONSTRAINT fk_entradas_butaca_funcion
        FOREIGN KEY (butaca_funcion_id) REFERENCES butacas_funcion(id),
    UNIQUE KEY uq_entradas_codigo_qr (codigo_qr)
);

CREATE TABLE IF NOT EXISTS compras_servicios (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    compra_id INT UNSIGNED NOT NULL,
    servicio_id INT UNSIGNED NOT NULL,
    cantidad INT UNSIGNED NOT NULL,
    precio_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    CONSTRAINT chk_compras_servicios_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_compras_servicios_precio CHECK (precio_unitario >= 0),
    CONSTRAINT chk_compras_servicios_subtotal CHECK (subtotal >= 0),
    CONSTRAINT fk_compras_servicios_compra
        FOREIGN KEY (compra_id) REFERENCES compras(id),
    CONSTRAINT fk_compras_servicios_servicio
        FOREIGN KEY (servicio_id) REFERENCES servicios(id),
    UNIQUE KEY uq_compras_servicios (compra_id, servicio_id)
);

