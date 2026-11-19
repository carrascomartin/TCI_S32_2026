"""Las claves no se versionan, son obligatorias y el error explica cómo definirlas."""

import tomllib
from pathlib import Path

import pytest

from autenticacion_jwt import validar_configuracion_jwt
from secretos import SecretoInvalidoError
from utils import load_config, update_config

SECRET_KEY = "AUTOCONFIG_SECRETS__SECRET_KEY"
CLAVE_JWT = "AUTOCONFIG_SECRETS__CLAVE_JWT"


def test_config_toml_no_trae_claves():
    secretos = tomllib.loads(Path("config.toml").read_text(encoding="utf-8")).get("secrets", {})

    assert secretos == {}


def test_sin_secret_key_el_error_explica_como_definirla(monkeypatch):
    monkeypatch.delenv(SECRET_KEY)

    with pytest.raises(SecretoInvalidoError) as error:
        load_config("default", reload=True)

    mensaje = str(error.value)
    assert "Falta configurar SECRET_KEY" in mensaje
    assert SECRET_KEY in mensaje
    assert ".env.example" in mensaje
    assert "token_urlsafe" in mensaje


def test_secret_key_en_blanco_cuenta_como_faltante(monkeypatch):
    monkeypatch.setenv(SECRET_KEY, "   ")

    with pytest.raises(SecretoInvalidoError, match="Falta configurar SECRET_KEY"):
        load_config("default", reload=True)


def test_secret_key_corta_se_rechaza_sin_mostrar_su_valor(monkeypatch):
    monkeypatch.setenv(SECRET_KEY, "123456")

    with pytest.raises(SecretoInvalidoError, match="6 bytes") as error:
        load_config("default", reload=True)

    assert "123456" not in str(error.value)


def test_la_secret_key_se_lee_de_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv(SECRET_KEY, "s" * 32)

    assert load_config("default", reload=True).secrets.SECRET_KEY == "s" * 32


def configuracion_jwt(algoritmo: str, largo_clave: int):
    base = load_config("default", reload=True)
    jwt = base.auth.JWT.model_copy(update={"HABILITADO": True, "ALGORITMO": algoritmo})
    return update_config(
        {
            "auth": base.auth.model_copy(update={"JWT": jwt}),
            "secrets": {"CLAVE_JWT": "x" * largo_clave},
        }
    )


@pytest.mark.parametrize(
    ("algoritmo", "minimo"), [("HS256", 32), ("HS384", 48), ("HS512", 64)]
)
def test_la_clave_jwt_exige_el_largo_del_algoritmo(algoritmo, minimo):
    validar_configuracion_jwt(configuracion_jwt(algoritmo, minimo))

    with pytest.raises(ValueError, match=f"{minimo} bytes") as error:
        validar_configuracion_jwt(configuracion_jwt(algoritmo, minimo - 1))

    assert CLAVE_JWT in str(error.value)


def test_con_jwt_habilitado_la_clave_jwt_no_puede_faltar():
    with pytest.raises(ValueError, match="tiene 0 bytes") as error:
        validar_configuracion_jwt(configuracion_jwt("HS256", 0))

    assert CLAVE_JWT in str(error.value)
