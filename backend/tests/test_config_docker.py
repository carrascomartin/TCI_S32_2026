"""config.docker.toml solo puede diferir de config.toml en la base de datos."""

import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def leer(nombre: str) -> dict:
    return tomllib.loads((RAIZ / nombre).read_text(encoding="utf-8"))


def test_docker_coincide_con_la_base_salvo_la_seccion_database():
    base, docker = leer("config.toml"), leer("config.docker.toml")
    assert {k: v for k, v in docker.items() if k != "database"} == {
        k: v for k, v in base.items() if k != "database"
    }


def test_docker_apunta_a_postgres_y_no_trae_la_contrasena():
    base = leer("config.docker.toml")["database"]
    assert (base["DB_TYPE"], base["DB_DRIVER"], base["DB_HOST"]) == ("postgresql", "asyncpg", "db")
    assert "DB_PASSWORD" not in base
