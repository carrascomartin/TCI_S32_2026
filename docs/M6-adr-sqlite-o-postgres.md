# ADR M6: base de datos del entregable, SQLite o PostgreSQL

- **Estado:** Propuesto
- **Fecha:** 2026-11-19
- **Decisores:** Elias Caracas, Martin Carrasco y Nicolás Pieroni
- **Relacionado:** [ADR T06](T06-adr-arquitectura.md) (arquitectura y stack), issue #94

## Contexto

El stack de la materia (`docs/cronograma_alumnos.md`) fija **SQLModel + Alembic + PostgreSQL** para los datos, y el ADR T06 declara PostgreSQL como base prevista. Hasta ahora el `docker-compose.yml` levantaba solo `backend` y `frontend`, y el backend usaba SQLite: un archivo `data/db.sqlite3` dentro del volumen `backend-data`.

La devolución de la cátedra marca esa diferencia como una brecha ("SQLite en compose, no Postgres") y pregunta: "¿SQLite o Postgres? Si mañana lo despliegan, ¿qué cambia? ¿Por qué el compose no levanta Postgres?". Este documento responde con pruebas hechas contra PostgreSQL, no con suposiciones.

Estado de la capa de datos, que no cambia con esta decisión: SQLModel sobre SQLAlchemy 2.0 en modo asíncrono, sin herramienta de migraciones (el esquema se crea al iniciar con `create_all`).

## Decisión

1. El entregable usa **PostgreSQL 16**: `docker compose up` levanta el servicio `db` y el backend se conecta con `asyncpg`.
2. **SQLite** se mantiene para desarrollar sin Docker y para la suite de tests, que lo usa directamente.
3. Cambiar de motor es un cambio de **configuración y de despliegue**, no de código de la aplicación. Lo verificamos (ver "Verificación").

## Por qué

- **Es el stack pedido.** El cronograma fija PostgreSQL y la cátedra marcó SQLite en el compose como una brecha.
- **El costo era bajo y está medido.** El código de la aplicación no cambia: `asyncpg` ya estaba en las dependencias y la base se elige por configuración. Antes de decidir se comparó el comportamiento de la API sobre los dos motores (ver "Verificación").
- **Lo que se demuestra es lo que se despliega.** Con SQLite en el compose, la demo mostraba un motor distinto del objetivo, y diferencias como la de la búsqueda con mayúsculas acentuadas (ver más abajo) quedaban ocultas hasta producción.

## Cómo quedó

| Qué | Sin Docker y en los tests | En Docker Compose |
| --- | --- | --- |
| Motor | SQLite, archivo `data/db.sqlite3` | PostgreSQL 16 (`postgres:16-alpine`), servicio `db` |
| Driver | `aiosqlite` | `asyncpg` |
| Configuración | `backend/config.toml` | `backend/config.docker.toml`, montado como `/app/config.toml` |
| Contraseña | No aplica | `POSTGRES_PASSWORD` del `.env`, que llega al backend como `AUTOCONFIG_DATABASE__DB_PASSWORD` |
| Datos | Archivo local | Volumen `pgdata`: `docker compose down` los conserva y `down -v` los borra |
| Arranque | Inmediato | El backend espera a que `db` esté sano (`pg_isready`) |

- `config.docker.toml` es igual a `config.toml` salvo la sección `[database]`, y no incluye la contraseña. `tests/test_config_docker.py` falla si los dos archivos difieren en otra sección, para que no se separen con el tiempo.
- Como el archivo se monta en el lugar de `config.toml`, los comandos del contenedor (`app.py`, `datos_prueba.py`, `gestionar_acceso.py`) usan PostgreSQL sin indicar `--config`.
- El puerto 5432 no se publica en el host: solo el backend habla con la base.
- La base arranca vacía. Los datos de prueba se cargan con el mismo comando de siempre, dentro del contenedor.
- Los datos que hubiera en el volumen viejo `backend-data` (SQLite) no se migran.

## Verificación

Se hizo el 19/11/2026 con PostgreSQL 16, en dos etapas.

**Comparación entre motores, antes de decidir** (con el compose de prueba y sin modificar el código):

1. **Misma carga de datos.** `datos_prueba.py cargar` terminó sin errores en los dos motores: 9 máquinas, 10 ubicaciones, 10 repuestos, 7 incidencias, 7 pedidos de compra y 15 movimientos de stock.
2. **Mismo esquema.** Los dos crearon las mismas 21 tablas, con 16 restricciones `CHECK` y 40 claves foráneas. La diferencia está en los tipos: PostgreSQL usa `timestamp with time zone` y `boolean`.
3. **Mismo comportamiento de la API.** Se hicieron 31 pedidos HTTP idénticos a un backend sobre cada motor (login, consultas, búsquedas, altas, ediciones y errores `404`, `409`, `422` y `403` por rol) y se compararon el código y el cuerpo, sin los valores de fecha. **29 respuestas fueron idénticas y 2 difirieron** (ver la sección siguiente). Las fechas tuvieron el mismo formato en los dos (`2026-09-20T12:47:17.954462Z`).
4. **Stock no negativo.** Un `UPDATE` que deja `cantidad_fisica` en `-1` es rechazado por la restricción `CHECK` en los dos motores.

**El compose del entregable** (en un proyecto de Compose aparte, con los endpoints de reservas incluidos):

5. El backend arrancó con `DatabaseType: postgresql` después de que `db` estuviera sano, y `datos_prueba.py cargar` funcionó dentro del contenedor sin `--config`.
6. Pasando por el nginx del frontend, como lo hace el navegador: el login y `GET` de máquinas (9), repuestos (10), ubicaciones (10) y reservas respondieron `200` con token y `401` sin token.
7. Reservas: crear una reserva bajó el disponible del repuesto de 4 a 1, una reserva mayor al disponible respondió `409 stock_insuficiente` sin cambios, el empleado recibió `403` al liberar, el encargado liberó (`200`) y la ejecución descontó lo consumido y liberó el resto.
8. Fallo en medio de una ejecución (RN-10): se borró la existencia de la segunda partida antes de ejecutar. La API respondió `409` y en PostgreSQL no quedó nada a medias: la primera existencia, los movimientos de consumo y el estado `activa` de la reserva siguieron iguales.
9. Tras `docker compose down` y `up`, las 4 reservas seguían en la base (el volumen `pgdata` conserva los datos).

No se verificó:

- La suite de tests contra PostgreSQL: 8 tests usan `sqlite3` directo y habría que reescribirlos.
- Las pantallas del frontend en el navegador contra este compose (sí las rutas de la API a través de su nginx).
- Incidencias, que todavía no están en `main`.
- Carga, concurrencia real, copias de seguridad, TLS ni otras versiones de PostgreSQL.
- Las migraciones de nombres heredadas de `_renombrar_tablas_autenticacion`, que solo aplican a bases creadas con el esquema anterior.

## Diferencias de comportamiento encontradas

1. **Búsqueda de repuestos con mayúsculas acentuadas.** `GET /api/v0/repuestos?buscar=VÁLVULA` devuelve el repuesto en PostgreSQL y ninguno en SQLite. SQLAlchemy traduce `ilike` a `lower(col) LIKE lower(?)` en SQLite, y el `lower()` de SQLite solo convierte caracteres ASCII (`lower('VÁLVULA')` da `vÁlvula`). Con minúsculas (`válvula`) los dos encuentran el repuesto, y sin el acento (`valvula`) ninguno. Con PostgreSQL en el compose, la demo se comporta como el motor objetivo; la diferencia queda solo para el desarrollo sin Docker.
2. **Claves foráneas en SQLite.** PostgreSQL siempre las exige. SQLite las exige solo si cada conexión activa `PRAGMA foreign_keys=ON`. La aplicación lo hace, pero una conexión externa (un cliente SQL o un script) no: en la prueba, SQLite aceptó una incidencia con una máquina inexistente.
3. **Fechas.** SQLite las guarda como texto sin zona horaria (siempre en UTC) y la capa de datos las vuelve a interpretar como UTC. PostgreSQL las guarda con zona horaria. La API devuelve el mismo formato.

## Alternativas consideradas

### SQLite también en el entregable

Era la propuesta inicial de este ADR: un servicio menos, sin contraseña de base y sin orden de arranque. Se descartó porque se aparta del stack pedido, oculta diferencias reales entre motores y su ventaja (menos pasos para levantar el proyecto) se resolvió igual: la contraseña va en el mismo `.env` que las claves y Compose ordena el arranque con el healthcheck.

### PostgreSQL también en los tests

Es lo más fiel al entorno objetivo, pero obliga a reescribir los 8 tests que usan `sqlite3` y a tener una base levantada para correr la suite. Queda como trabajo pendiente.

### SQLite en producción

Sirve para una sola instancia con poca escritura concurrente. No sirve para varias instancias del backend ni para mucha escritura simultánea, porque admite un solo escritor a la vez.

## Consecuencias positivas

- El entregable usa el motor del stack pedido y el mismo que tendría producción.
- La portabilidad está comprobada en los dos sentidos, con las diferencias entre motores registradas.
- `docker compose up` sigue siendo un solo comando desde un clone limpio, con un valor más en el `.env`.

## Consecuencias negativas y riesgos

- La suite de tests corre sobre SQLite, no sobre el motor del entregable. Una diferencia entre motores puede pasar los tests y fallar en Docker.
- Sin Alembic (que el stack también pide), un cambio de esquema sobre una base con datos requiere trabajo manual, ahora sobre PostgreSQL.
- Quien ya tenía el proyecto levantado tiene que agregar `POSTGRES_PASSWORD` al `.env` y volver a cargar los datos de prueba.
- `docker compose down -v` borra la base y no hay copia de seguridad automática.
- La concurrencia de RN-01 (que el stock no quede negativo cuando dos empleados descuentan la última unidad) sigue sin decidirse (`docs/dominio/dominio.md`, sección 7, hueco 2). Las reservas ya actualizan las existencias con una sola sentencia condicionada en la base, que ese ADR puede tomar como punto de partida.

## Alcance de esta decisión

Este ADR decide qué base usa el entregable y cómo se configura. No define:

- La incorporación de Alembic ni la estrategia de migraciones.
- La migración de la suite de tests a PostgreSQL.
- Las copias de seguridad ni la configuración de producción de PostgreSQL.
- La decisión de concurrencia de RN-01.
