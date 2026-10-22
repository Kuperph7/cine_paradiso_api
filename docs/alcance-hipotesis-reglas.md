# Cine Paradiso — Alcance, hipótesis y reglas de negocio

*Documento para el Hito 1 — Borrador para validar con el equipo*

## 1. Objetivo del sistema

Desarrollar una aplicación web para que los clientes consulten la cartelera, elijan funciones y butacas disponibles, compren entradas y servicios adicionales, y reciban la confirmación de compra. Los administradores podrán gestionar películas, locales, salas, funciones y servicios, además de consultar estadísticas.

## 2. Alcance del sistema

### 2.1. Funcionalidades principales

**Clientes**

- Consultar películas, información y funciones disponibles.
- Consultar la disponibilidad de butacas y seleccionar butacas para una función.
- Comprar entradas y servicios adicionales, como comida, bebidas, estacionamiento o acceso VIP.
- Recibir por correo electrónico la confirmación, la factura y el código QR de ingreso.
- Consultar su perfil, consumos y películas vistas anteriormente.
- Solicitar la cancelación de una entrada dentro del plazo establecido.

**Administradores**

- Gestionar películas y su información.
- Configurar locales, salas y funciones.
- Crear, modificar y dar de baja servicios adicionales.
- Consultar estadísticas de ocupación, ventas según el género cinematográfico (por ejemplo, acción, comedia o drama), franjas horarias y cancelaciones.
- Validar los códigos QR de las entradas en el acceso.

### 2.2. Funcionalidades adicionales acordadas por el equipo

El equipo acordó realizar estas funcionalidades después de implementar las principales:

- Permitir puntuar o reseñar películas únicamente a usuarios cuya entrada para la función haya sido validada mediante QR.
- Generar un PDF con ventas por función y películas más vistas.
- Dockerizar el proyecto.
- Desplegar la aplicación y la base de datos en servicios gratuitos.

## 3. Hipótesis, supuestos y puntos pendientes

La consigna establece que Cine Paradiso tiene tres locales; contempla clientes y administradores; cada función corresponde a una película, sala, fecha y hora; las butacas no se pueden vender dos veces para una misma función; y la cancelación solo se permite hasta cierto plazo antes de la función. También requiere confirmaciones por correo, factura y QR de ingreso.

Los siguientes detalles no están definidos por completo y deben acordarse en el equipo:

- El plazo exacto para cancelar una entrada.
- Si se generará un código QR por entrada o uno por compra.
- La escala y los criterios concretos para puntuar o reseñar películas.
- El criterio para determinar cuáles son las películas más vistas, por ejemplo, según las entradas vendidas o las entradas efectivamente validadas.

## 4. Reglas de negocio

- **RN-01. Roles:** las funciones de administración estarán disponibles solo para usuarios con rol administrador.
- **RN-02. Función:** cada función estará asociada a una película, una sala y una fecha y hora determinadas.
- **RN-03. Butacas:** una misma butaca no podrá venderse más de una vez para la misma función.
- **RN-04. Disponibilidad:** la disponibilidad de una butaca se comprobará para la función seleccionada.
- **RN-05. Cancelación:** una entrada solo podrá cancelarse dentro del plazo anterior al inicio de la función que defina el equipo.
- **RN-06. Confirmación:** una compra completada deberá generar el envío por correo de la confirmación, la factura y el QR de ingreso.
- **RN-07. Validación del QR:** el QR deberá corresponder a la función y fecha pertinentes; la entrada no podrá estar cancelada ni utilizada. Tras una validación exitosa, deberá marcarse como utilizada.
- **RN-08. Servicios:** el administrador podrá crear, modificar y dar de baja servicios; los servicios configurados estarán disponibles para todas las salas.
- **RN-09. Seguridad:** los endpoints deberán verificar los permisos de acceso y restringir las operaciones administrativas a los usuarios con rol administrador.
- **RN-10. Reseñas:** solo podrán puntuar o reseñar una película los usuarios cuya entrada para la función correspondiente haya sido validada mediante QR.