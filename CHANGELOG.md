# Changelog

Registro de cambios relevantes del proyecto. Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Security

- `SECRET_KEY` y `CLAVE_JWT` ya no están en `config.toml` (traía `SECRET_KEY = "123456"` y `CLAVE_JWT` vacía). Se leen de las variables `AUTOCONFIG_SECRETS__SECRET_KEY` y `AUTOCONFIG_SECRETS__CLAVE_JWT`; `docker compose` las toma de un `.env` que no se versiona (issue #92, M6). `SECRET_KEY` es obligatoria y exige 32 bytes; si falta o es corta, el backend aborta con un mensaje que explica cómo definirla. Verificado con `docker compose`: el backend arranca con las claves, `POST /auth/token` responde `400` (login activo) y la API sin token responde `401`; sin las claves, la imagen termina con código `1` y el mensaje. `CLAVE_JWT` ya exigía 32/48/64 bytes según el algoritmo, pero no tenía tests: ahora se prueba el límite exacto.

### Changed

- `docker compose up` requiere un `.env` con `SECRET_KEY` y `CLAVE_JWT` (copiar `.env.example`). El compose activa el JWT local con `AUTOCONFIG_AUTH__JWT__HABILITADO=true`; `config.toml` ya no define `HABILITADO` (el valor por defecto sigue siendo `false`) porque el archivo gana sobre la variable.

### Fixed

- Las variables de entorno `AUTOCONFIG_*` nunca funcionaron: se leían en minúsculas y los campos de la configuración están en mayúsculas, así que el modelo las rechazaba y definir cualquiera hacía fallar la carga de toda la configuración. Ahora se resuelven al nombre real del campo, sin distinguir mayúsculas.

### Added

- `docker-compose.yml` en la raíz, con `Dockerfile` para `backend/` (Python 3.14 + uv) y `frontend/` (build de Angular servido con nginx). `docker compose up --build` levanta todo el stack desde un clone limpio (issue #29, M2). Verificado de punta a punta: backend responde `200` en `/health`, frontend responde `200` en `http://localhost:8080`.
- `.dockerignore` en `backend/` y `frontend/` para no copiar `node_modules`, `.venv`, `dist` ni logs al build.
- Sección "Cómo levantar el proyecto con Docker" en el README principal, más una sección de Docker en `backend/README.md` y `frontend/README.md`.
- `docs/M6-adr-sqlite-o-postgres.md`: ADR que explica por qué el compose usa SQLite y qué cambia para pasar a PostgreSQL (issue #94, M6). Verificado contra PostgreSQL 16: la misma carga de datos y 31 pedidos HTTP a un backend sobre cada motor dieron 29 respuestas idénticas; las 2 diferencias (búsqueda de repuestos con mayúsculas acentuadas) y lo que no se verificó figuran en el documento.
