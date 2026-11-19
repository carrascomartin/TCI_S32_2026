"""Las variables de entorno AUTOCONFIG_* llegan a los campos en mayúsculas de la configuración."""

import pytest
from pydantic import ValidationError

from config import Config

TOML_MINIMO = "[server]\n[secrets]\n[database]\n[logs]\n"
CLAVE = "k" * 40


def cargar(tmp_path, toml: str, env: dict[str, str]) -> Config:
    ruta = tmp_path / "config.toml"
    ruta.write_text(toml, encoding="utf-8")
    return Config.maker.load(path=ruta, env=env)


def test_la_variable_llega_a_campos_en_mayusculas_y_anidados(tmp_path):
    config = cargar(
        tmp_path,
        TOML_MINIMO,
        {
            "AUTOCONFIG_SECRETS__SECRET_KEY": CLAVE,
            "AUTOCONFIG_SECRETS__CLAVE_JWT": CLAVE.upper(),
            "AUTOCONFIG_AUTH__JWT__HABILITADO": "true",
            "AUTOCONFIG_SERVER__PORT": "9001",
        },
    )

    assert config.secrets.SECRET_KEY == CLAVE
    assert config.secrets.CLAVE_JWT == CLAVE.upper()
    assert config.auth.JWT.HABILITADO is True
    assert config.server.PORT == 9001


def test_el_archivo_gana_sobre_la_variable(tmp_path):
    config = cargar(
        tmp_path,
        TOML_MINIMO.replace("[secrets]", '[secrets]\nSECRET_KEY = "del-archivo"'),
        {"AUTOCONFIG_SECRETS__SECRET_KEY": CLAVE},
    )

    assert config.secrets.SECRET_KEY == "del-archivo"


def test_una_variable_que_no_corresponde_a_ningun_campo_se_rechaza(tmp_path):
    with pytest.raises(ValidationError, match="no_existe"):
        cargar(
            tmp_path,
            TOML_MINIMO,
            {
                "AUTOCONFIG_SECRETS__SECRET_KEY": CLAVE,
                "AUTOCONFIG_SECRETS__NO_EXISTE": "x",
            },
        )
