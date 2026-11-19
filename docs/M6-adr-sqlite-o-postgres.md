# ADR M6: base de datos del entregable, SQLite o PostgreSQL

- **Estado:** Propuesto
- **Fecha:** 2026-11-19
- **Decisores:** Elias Caracas, Martin Carrasco y Nicolás Pieroni
- **Relacionado:** [ADR T06](T06-adr-arquitectura.md) (arquitectura y stack), issue #94

## Contexto

El ADR T06 declara PostgreSQL como base de datos prevista para el entorno objetivo. El `docker-compose.yml` del proyecto levanta solo `backend` y `frontend`, y el backend usa SQLite: un archivo `data/db.sqlite3` dentro del volumen `backend-data` (`config.toml`: `DB_TYPE = "sqlite3"`, `DB_DRIVER = "aiosqlite"`).

La devolución de la cátedra marca esta diferencia como una brecha ("SQLite en compose, no Postgres") y pregunta: "¿SQLite o Postgres? Si mañana lo despliegan, ¿qué cambia?". Este documento responde las dos preguntas con una prueba hecha contra PostgreSQL, no con suposiciones.

Estado actual de la capa de datos, que no cambia con esta decisión: SQLModel sobre SQLAlchemy 2.0 en modo asíncrono, y sin herramienta de migraciones (el esquema se crea al iniciar con `create_all`).

## Decisión

1. El entregable de M6 usa **SQLite**, en un archivo dentro de un volumen de Docker.
2. **PostgreSQL** sigue siendo la base objetivo para producción, como dice T06.
3. Pasar de una a otra es un cambio de **configuración y de despliegue**, no de código de la aplicación. Lo verificamos (ver "Verificación").
4. No se agrega un servicio PostgreSQL al compose del entregable. La receta verificada para hacerlo está en este documento.

## Por qué el compose no levanta PostgreSQL

- **Reproducibilidad de la entrega.** Hoy `docker compose up` levanta dos contenedores desde un clone limpio. PostgreSQL agrega un tercer servicio, una contraseña, un volumen y un orden de arranque (la base tiene que estar lista antes que el backend). Son más pasos que pueden fallar durante la entrega y la demo.
- **Escala del problema.** El sistema es un prototipo con pocos usuarios y poca escritura simultánea. SQLite alcanza y no es el límite del sistema.
- **No hay migraciones.** El esquema se crea al iniciar y no hay Alembic. Con datos que deban sobrevivir a cambios de esquema, PostgreSQL sin migraciones no mejora a SQLite y suma riesgo.
- **La suite de tests está atada a SQLite.** 8 de los 27 tests usan `sqlite3` directamente. Cambiar el motor del entregable obliga a reescribirlos.
- **Plazo.** El congelamiento es el 20/11. No conviene cambiar infraestructura en la última semana.

## Qué cambia si mañana lo despliegan con PostgreSQL

| Qué | Hoy (SQLite) | Con PostgreSQL | Verificado |
| --- | --- | --- | --- |
| Driver | `aiosqlite` | `asyncpg`: ya está en `pyproject.toml` (0.31.0) y dentro de la imagen del backend | Sí |
| Configuración | `[database]` con `DB_TYPE = "sqlite3"` y `DB_NAME = "data/db.sqlite3"` | `DB_TYPE = "postgresql"`, `DB_DRIVER = "asyncpg"`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME`, en un `config.<entorno>.toml` | Sí |
| Compose | Volumen `backend-data` con el archivo | Servicio `db` con volumen `pgdata`, healthcheck y `depends_on`; el backend deja de usar `backend-data` | Sí |
| Código de la aplicación | Sin cambios | Sin cambios: los dos puntos propios de SQLite en `db/database.py` (`check_same_thread` y `PRAGMA foreign_keys=ON`) ya se aplican solo cuando el motor es SQLite | Sí |
| Esquema | `create_all` | `create_all` crea las mismas 21 tablas | Sí |
| Datos de prueba | `datos_prueba.py cargar` | El mismo comando, sin cambios | Sí |
| Migraciones | No hay | Hay que incorporar Alembic antes de producción | No aplica |
| Tests | 8 de 27 usan `sqlite3` | Reemplazar esos accesos por la sesión de SQLAlchemy para correrlos contra PostgreSQL | No |

### Receta de Compose

Se usa un archivo aparte que se suma al compose existente: `docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d db backend`. La contraseña es la misma en `POSTGRES_PASSWORD` y en `DB_PASSWORD` del archivo de configuración, y ese archivo no se versiona: `config.*.toml` está en el `.gitignore` y el `.dockerignore` del backend.

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: tci
      POSTGRES_PASSWORD: <contraseña>
      POSTGRES_DB: tci
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tci -d tci"]
      interval: 5s
      timeout: 3s
      retries: 10
  backend:
    volumes: !override
      - ./backend/config.postgres.toml:/app/config.toml:ro
    depends_on:
      db:
        condition: service_healthy
volumes:
  pgdata:
```

Las claves `SECRET_KEY` y `CLAVE_JWT` siguen llegando por el `.env` de la raíz (ver el README), igual que con SQLite, así que `config.postgres.toml` no las lleva.

`config.postgres.toml` es una copia de `config.toml` con `[database]` apuntando al servicio `db`: `DB_TYPE = "postgresql"`, `DB_DRIVER = "asyncpg"`, `DB_HOST = "db"`, `DB_PORT = 5432`, `DB_USER = "tci"`, `DB_NAME = "tci"` y la contraseña.

## Verificación

Se hizo el 19/11/2026 con PostgreSQL 16, sin modificar el código del proyecto.

1. **Misma carga de datos en los dos motores.** `datos_prueba.py cargar` terminó sin errores en ambos: 9 máquinas, 10 ubicaciones, 10 repuestos, 7 incidencias, 7 pedidos de compra y 15 movimientos de stock.
2. **Mismo esquema.** Ambos crearon las mismas 21 tablas, con 16 restricciones `CHECK` y 40 claves foráneas definidas. La diferencia está en los tipos: PostgreSQL usa `timestamp with time zone` y `boolean`.
3. **Mismo comportamiento de la API.** Se hicieron 31 pedidos HTTP idénticos a un backend sobre cada motor (login, consultas, búsquedas, altas, ediciones, errores `404`, `409`, `422` y `403` por rol) y se compararon el código y el cuerpo, sin comparar los valores de las fechas. **29 respuestas fueron idénticas y 2 difirieron** (ver la sección siguiente). El formato de las fechas fue el mismo en ambos (`2026-09-20T12:47:17.954462Z`).
4. **Stock no negativo.** Un `UPDATE` que deja `cantidad_fisica` en `-1` es rechazado por la restricción `CHECK` en los dos motores.
5. **Receta de Compose.** Con la receta de arriba (con la ruta del archivo de configuración y el puerto adaptados al entorno de prueba), el backend levantó con `DatabaseType: postgresql`, esperó a que la base estuviera sana, cargó los datos de prueba desde dentro del contenedor y respondió la API con autenticación. Tras `docker compose down` y `up`, los 10 repuestos seguían ahí (el volumen `pgdata` conserva los datos).

No se verificó:

- La suite de tests contra PostgreSQL (no corre sin reescribir los 8 tests que usan `sqlite3`).
- El frontend contra el compose con PostgreSQL. No se levantó, aunque solo habla HTTP con el backend.
- Carga, concurrencia real, copias de seguridad, TLS ni otras versiones de PostgreSQL.
- Las migraciones de nombres heredadas de `_renombrar_tablas_autenticacion`, que solo aplican a bases creadas con el esquema anterior.

## Diferencias de comportamiento encontradas

1. **Búsqueda de repuestos con mayúsculas acentuadas.** `GET /api/v0/repuestos?buscar=VÁLVULA` devuelve el repuesto en PostgreSQL y ninguno en SQLite. SQLAlchemy traduce `ilike` a `lower(col) LIKE lower(?)` en SQLite, y el `lower()` de SQLite solo convierte caracteres ASCII (`lower('VÁLVULA')` da `vÁlvula`). Con minúsculas (`válvula`) ambos encuentran el repuesto, y sin el acento (`valvula`) ninguno lo encuentra. Quedó fuera de esta decisión; corregirlo requiere normalizar el texto antes de buscar.
2. **Claves foráneas en SQLite.** PostgreSQL siempre las exige. SQLite las exige solo si cada conexión activa `PRAGMA foreign_keys=ON`. La aplicación lo hace, pero una conexión externa (un cliente SQL o un script) no: en la prueba, SQLite aceptó una incidencia con una máquina inexistente.
3. **Fechas.** SQLite las guarda como texto sin zona horaria (siempre en UTC) y la capa de datos las vuelve a interpretar como UTC. PostgreSQL las guarda con zona horaria. La API devuelve el mismo formato.

## Alternativas consideradas

### PostgreSQL en el compose del entregable

Es igual al entorno objetivo, tiene tipos y restricciones más estrictos y admite escrituras concurrentes. Se descartó por ahora por las razones de la sección "Por qué el compose no levanta PostgreSQL". Queda a un archivo de distancia: la receta está verificada.

### SQLite también en producción

Sirve para una sola instancia del backend con poca escritura concurrente. No sirve para varias instancias (un archivo no se comparte de forma segura entre procesos en distintos hosts) ni para mucha escritura simultánea, porque SQLite admite un solo escritor a la vez. No lo recomendamos para producción.

## Consecuencias positivas

- El entregable se levanta con un solo comando y sin servicios extra.
- La portabilidad está comprobada y no solo declarada: pasar a PostgreSQL es un cambio de configuración, con una receta que ya funcionó.
- Quedan registradas las diferencias de comportamiento entre los dos motores.

## Consecuencias negativas y riesgos

- Los datos del entregable viven en un archivo dentro de un volumen: `docker compose down -v` los borra y no hay copia de seguridad automática.
- SQLite admite un solo escritor a la vez, así que no escala a varias instancias del backend.
- Desarrollar sobre SQLite puede ocultar diferencias hasta que se cambie de motor, como la búsqueda con mayúsculas acentuadas.
- Sin Alembic, un cambio de esquema sobre una base con datos requiere trabajo manual en cualquiera de los dos motores.
- La suite de tests no cubre PostgreSQL.
- La concurrencia de RN-01 (que el stock no quede negativo cuando dos empleados descuentan la última unidad) sigue sin decidirse (`docs/dominio/dominio.md`, sección 7, hueco 2). La restricción `CHECK` protege en ambos motores, pero una lectura seguida de una escritura se comporta distinto en cada uno, así que esa decisión tendrá que tomar en cuenta el motor.

## Alcance de esta decisión

Este ADR decide qué base usa el entregable y documenta el paso a PostgreSQL. No define:

- La estrategia de migraciones ni la incorporación de Alembic.
- Las copias de seguridad ni la configuración de producción de PostgreSQL.
- La decisión de concurrencia de RN-01.
