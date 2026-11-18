-- Arregla las tildes rotas (ficciÃ³n -> ficción) en TODAS las tablas de la base.
-- No borra nada: solo corrige las filas que tienen "Ã". Se puede correr más de una vez.
SET NAMES utf8mb4;
SET SQL_SAFE_UPDATES = 0;

DROP PROCEDURE IF EXISTS arreglar_tildes;

DELIMITER $$
CREATE PROCEDURE arreglar_tildes()
BEGIN
  DECLARE fin INT DEFAULT 0;
  DECLARE v_tabla VARCHAR(64);
  DECLARE v_columna VARCHAR(64);
  DECLARE cur CURSOR FOR
    SELECT c.table_name, c.column_name
    FROM information_schema.columns c
    JOIN information_schema.tables t
      ON t.table_schema = c.table_schema AND t.table_name = c.table_name
    WHERE c.table_schema = DATABASE()
      AND t.table_type = 'BASE TABLE'
      AND c.character_set_name = 'utf8mb4'
      AND c.data_type IN ('char','varchar','tinytext','text','mediumtext','longtext');
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET fin = 1;

  OPEN cur;
  recorrer: LOOP
    FETCH cur INTO v_tabla, v_columna;
    IF fin = 1 THEN LEAVE recorrer; END IF;
    SET @sentencia = CONCAT(
      'UPDATE `', v_tabla, '` SET `', v_columna,
      '` = CONVERT(CAST(CONVERT(`', v_columna, '` USING latin1) AS BINARY) USING utf8mb4)',
      ' WHERE `', v_columna, '` COLLATE utf8mb4_bin LIKE ''%Ã%''');
    PREPARE paso FROM @sentencia;
    EXECUTE paso;
    DEALLOCATE PREPARE paso;
  END LOOP;
  CLOSE cur;
END$$
DELIMITER ;

CALL arreglar_tildes();
DROP PROCEDURE arreglar_tildes;
