# Actores del dominio

> T08. Formaliza los actores ya descriptos en `docs/dominio/dominio.md` (sección 3), agregando permisos y la relación con las pantallas construidas hasta ahora.

## Los 4 roles

| Rol | Qué hace | Acceso |
| --- | --- | --- |
| **Operario de máquina** | Reporta incidencias y solicita reparaciones (fotos + QR de la máquina), en cualquier turno. | Alta de incidencias. Sin acceso a stock ni a compras. |
| **Empleado de mantenimiento** | Ingresa repuestos al almacén (escaneo), consulta existencia y registra el uso de repuestos en una reparación. También puede generar pedidos de compra para reportar faltantes. | Lectura y escritura sobre repuestos/stock y líneas de uso. Puede generar pedidos de compra, pero no gestionarlos ni aprobarlos. Sin acceso a gestionar usuarios. |
| **Encargado de mantenimiento** | Mantiene la lista de compras, asigna responsables, revisa, aprueba y cancela pedidos de compra. Carga el stock recibido (o delega y supervisa) y autoriza la liberación de reservas. | Lectura y escritura sobre pedidos de compra y recepciones. Única autoridad para liberar una reserva (RN-05) y gestionar pedidos de compra (CUN-03). |
| **Gerencia / Administración** | Solo lectura: tableros de seguimiento y consulta de información, incluidos los pedidos de compra. | Acceso de consulta. No puede crear, modificar, asignar, revisar, aprobar ni cancelar pedidos de compra. |

## Permisos por rol y pantalla construida

| Pantalla | Operario | Empleado de mantenimiento | Encargado | Gerencia/Administración |
| --- | --- | --- | --- | --- |
| Reportar incidencia (T16) | Alta | — | — | — |
| Registrar uso de repuesto (T17, CUN-01) | — | Alta | — | — |
| Consulta de incidencias (T13) | Lectura | Lectura | Lectura | Lectura |
| Consulta de repuestos / stock (T12) | — | Lectura | Lectura | Lectura |
| Reposición de repuestos (T14) | — | Lectura | Lectura | Lectura |
| Generar pedido de compra (T15) | — | Alta (reporta faltante) | Lectura/gestión | Lectura |
| Consultar pedidos de compra (T18) | — | — | Lectura | Lectura |
| Asignar responsable de pedido (CUN-03) | — | — | Escritura | — |
| Revisar pedido de compra (CUN-03) | — | — | Escritura | — |
| Aprobar pedido de compra (CUN-03) | — | — | Escritura | — |
| Cancelar pedido de compra (CUN-03) | — | — | Escritura | — |
| Consultar máquinas (T19) | — | Lectura | Lectura | Lectura |
| Cargar stock recibido con ubicación (RN-08, pendiente — issue #27) | — | — | Alta (o delega) | — |

El encargado de mantenimiento es el único rol autorizado para gestionar los pedidos de compra existentes: asignar responsables, revisarlos, aprobarlos y cancelarlos. Gerencia/Administración puede consultar los pedidos, pero no modificarlos. El empleado de mantenimiento puede generar pedidos para reportar faltantes, pero no tiene acceso a la gestión de los pedidos existentes. El operario no tiene acceso al módulo.

## Permisos de la API de repuestos y ubicaciones (T28)

El backend verifica estos roles en cada solicitud, leyéndolos de la base (no del token). Sin token responde `401`; con un rol sin permiso, `403`.

| Operación | Operario | Empleado de mantenimiento | Encargado | Gerencia/Administración |
| --- | --- | --- | --- | --- |
| Listar, buscar y consultar repuestos (`GET /repuestos`, `/repuestos/{id}`, `/repuestos/codigo/{codigo}`) | — | Sí | Sí | Sí |
| Crear y actualizar repuestos (`POST /repuestos`, `PATCH /repuestos/{id}`) | — | Sí | Sí | — |
| Listar ubicaciones (`GET /ubicaciones`) | — | Sí | Sí | Sí |
| Crear ubicaciones (`POST /ubicaciones`) | — | Sí | Sí | — |

El empleado mantiene el catálogo porque es quien ingresa repuestos al almacén; el encargado, porque carga el stock recibido y su ubicación (RN-08). Gerencia solo consulta y el operario no accede al almacén.

## Permisos de la API de incidencias (T29)

Acordado con el equipo el 19/11: solo el operario reporta; todos los roles consultan, el operario incluido, para seguir sus reportes. El frontend muestra "Reportar incidencia" solo al operario.

| Operación | Operario | Empleado de mantenimiento | Encargado | Gerencia/Administración |
| --- | --- | --- | --- | --- |
| Reportar una incidencia (`POST /incidencias`) | Sí | — | — | — |
| Listar y consultar incidencias (`GET /incidencias`, `/incidencias/{id}`) | Sí | Sí | Sí | Sí |

## Permisos de la API de reparaciones (CUN-01)

El empleado de mantenimiento es quien repara: toma la incidencia, registra los repuestos usados (RN-01) y la resuelve con el informe. Encargado y gerencia consultan; el operario sigue el estado de su incidencia, pero no ve la reparación.

| Operación | Operario | Empleado de mantenimiento | Encargado | Gerencia/Administración |
| --- | --- | --- | --- | --- |
| Tomar una incidencia (`POST /incidencias/{id}/reparacion`) | — | Sí | — | — |
| Registrar un repuesto usado (`POST /reparaciones/{id}/usos`) | — | Sí | — | — |
| Finalizar con el informe (`POST /reparaciones/{id}/informe`) | — | Sí | — | — |
| Consultar una reparación (`GET /reparaciones/{id}`) | — | Sí | Sí | Sí |

## Permisos de la API de reservas (RN-05 y RN-10)

| Operación | Operario | Empleado de mantenimiento | Encargado | Gerencia/Administración |
| --- | --- | --- | --- | --- |
| Listar y consultar reservas (`GET /reservas`, `/reservas/{id}`) | — | Sí | Sí | Sí |
| Crear una reserva (`POST /reservas`) | — | Sí | Sí | — |
| Ejecutar una reserva (`POST /reservas/{id}/ejecucion`) | — | Sí | Sí | — |
| Liberar una reserva (`POST /reservas/{id}/liberacion`) | — | — | Sí | — |

Solo el encargado libera una reserva (RN-05) y queda registrado como quien la autorizó. El empleado crea y ejecuta las reservas porque es quien hace el mantenimiento. El aviso inmediato de la liberación depende del puerto de notificación (RN-09) y todavía no está implementado.

## Permisos de la API de pedidos de compra (CUN-03)

| Operación | Operario | Empleado de mantenimiento | Encargado | Gerencia/Administración |
| --- | --- | --- | --- | --- |
| Listar pedidos de compra | — | — | Sí | Sí |
| Consultar detalle de un pedido | — | — | Sí | Sí |
| Crear pedidos de compra | — | Sí | Según permisos del caso de uso | — |
| Asignar responsable | — | — | Sí | — |
| Revisar pedidos | — | — | Sí | — |
| Aprobar pedidos | — | — | Sí | — |
| Cancelar pedidos | — | — | Sí | — |

El encargado de mantenimiento es el único rol que puede asignar responsables, revisar, aprobar y cancelar pedidos de compra. Gerencia/Administración tiene permisos exclusivamente de consulta. El operario no tiene acceso al módulo. El empleado de mantenimiento puede generar pedidos para informar faltantes, pero no puede consultar ni gestionar los pedidos existentes.

Las operaciones de gestión requieren autenticación y autorización. Sin token, la API responde `401`; si el usuario autenticado no tiene permisos suficientes, responde `403`.

## Fuente

- `docs/dominio/dominio.md`, sección 3 (actores) y sección 7, decisión 1 (fusión de Gerencia y Administración).
- Issues cerradas de frontend (T11 a T20) para la columna de pantallas.
- CUN-03: aprobación y cancelación de pedidos de compra y permisos por rol.