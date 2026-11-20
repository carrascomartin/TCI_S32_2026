# Guion de demostración

## Pedidos de compra (CUN-03)

### Preparación
- Levantar el entorno con `docker compose up -d`.
- Contar con pedidos de compra en estado `pendiente_aprobacion`.
- Disponer de usuarios habilitados para los roles encargado de mantenimiento y gerencia.

### Demostración

1. Iniciar sesión como **encargado de mantenimiento**.
2. Entrar a **Pedidos de compra** y consultar los pedidos existentes.
3. Seleccionar un pedido en estado `pendiente_aprobacion` y aprobarlo.
4. Verificar que su estado cambie a `confirmado`.
5. Seleccionar otro pedido pendiente de aprobación y cancelarlo indicando un motivo.
6. Verificar que su estado cambie a `cancelado` y que el motivo quede registrado.
7. Cerrar sesión e iniciar como **gerencia**.
8. Consultar los pedidos y comprobar que puede visualizar la información, pero no aprobarlos ni cancelarlos.

### Resultado esperado

- El encargado de mantenimiento puede aprobar y cancelar pedidos pendientes de aprobación.
- La aprobación cambia el estado a `confirmado`.
- La cancelación requiere un motivo y cambia el estado a `cancelado`.
- Gerencia puede consultar los pedidos, pero no modificarlos.
- Los roles sin permisos no pueden ejecutar estas operaciones.