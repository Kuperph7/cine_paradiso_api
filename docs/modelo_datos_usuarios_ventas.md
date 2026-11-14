Reglas de negocio — Modelo de usuarios y ventas


1. Gestión de cancelaciones
El sistema permitirá cancelar entradas dentro del plazo establecido antes del inicio de la función.

Para registrar una cancelación se utilizarán los campos estado y fecha_hora_cancelacion de la tabla entradas.

Cuando se realice una cancelación válida:

La entrada cambiará su estado a cancelada.
Se registrará la fecha y hora de cancelación.
El código QR asociado dejará de ser válido.
La butaca correspondiente volverá a estar disponible para esa función, actualizando el estado en butacas_funcion.

La entrada no se eliminará de la base de datos, ya que se debe conservar el historial de compras y cancelaciones.

Pendiente de definir: el plazo máximo de cancelación y si se permitirá cancelar entradas individuales de una compra.


2. Gestión y validación de códigos QR
Cada entrada podrá identificarse mediante un código único, almacenado en el campo codigo_qr de la tabla entradas.

Cuando un administrador escanee el QR, el sistema deberá:

Identificar la entrada correspondiente.
Comprobar que pertenezca a la función y fecha correctas.
Verificar que la entrada no esté cancelada.
Verificar que no haya sido utilizada anteriormente.

Si todas las comprobaciones son correctas, se permitirá el ingreso, se marcará la entrada como utilizada y se registrará el momento de validación en fecha_hora_validacion.

Si alguna condición no se cumple, se rechazará la validación.

Pendiente de definir: si se generará un QR por entrada o por compra. El diseño actual contempla un código por entrada.


3. Prevención de venta duplicada de butacas
Para controlar la disponibilidad de las butacas se utilizará la tabla butacas_funcion, que relaciona cada butaca con una función específica.

Esta tabla contiene los campos funcion_id, butaca_id y estado.

Se establecerá una restricción UNIQUE (funcion_id, butaca_id) para impedir que una misma butaca aparezca duplicada dentro de una función.

Antes de confirmar una compra, el sistema deberá:

Verificar que la butaca pertenezca a la sala de la función seleccionada.
Comprobar que esté disponible para esa función.
Registrar la ocupación y confirmar la compra mediante una operación transaccional segura, para impedir que dos compradores simultáneos adquieran la misma butaca.

Cuando se cancele una entrada, la ocupación podrá liberarse para permitir una nueva compra, conservando el historial de la entrada cancelada.

De esta manera, una butaca podrá venderse para distintas funciones, pero nunca dos veces de forma activa para una misma función. 
