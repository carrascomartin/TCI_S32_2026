from pathlib import Path

import pytest
from autoconfig import ConfigMaker

from config import Config, Database
from db.database import _build_engine
from utils import _config_path, load_config, update_config


def test_config_definition_generates_without_runtime_metadata(tmp_path: Path):
    path = ConfigMaker(Config, tmp_path).generate()
    text = path.read_text(encoding="utf-8")

    assert "[server]" in text
    assert "[database]" in text
    assert "\nNAME =" not in text
    assert "\nCONFIG_FILE =" not in text


def test_existing_template_loads_through_autoconfig():
    config = load_config("default", reload=True)

    assert isinstance(config, Config)
    assert config.server.PORT == 8300
    assert config.NAME == "config"
    assert config.CONFIG_FILE.name == "config.toml"


def test_runtime_overrides_keep_nested_models():
    config = load_config("default", reload=True)
    updated = update_config({"server": {"PORT": 9999}})

    assert updated.server.PORT == 9999
    assert updated.database.DB_NAME == config.database.DB_NAME


def test_entorno_resuelve_desde_backend_sin_depender_del_directorio(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raiz_backend = Path(__file__).resolve().parent.parent
    assert _config_path("dev") == raiz_backend / "config.dev.toml"
    assert _config_path("default") == raiz_backend / "config.toml"
    assert load_config("default", reload=True).CONFIG_FILE == raiz_backend / "config.toml"


def test_entorno_inexistente_no_carga_valores_por_defecto():
    with pytest.raises(FileNotFoundError, match="config.entorno-inexistente.toml"):
        load_config("entorno-inexistente", reload=True)


def test_driver_sqlite_invalido_indica_como_corregirlo():
    load_config("default", reload=True)
    update_config({"database": {"DB_DRIVER": "..."}})
    try:
        with pytest.raises(ValueError, match="DB_DRIVER.*aiosqlite"):
            _build_engine()
    finally:
        load_config("default", reload=True)


def test_engine_sqlite_se_construye_con_driver_async():
    load_config("default", reload=True)
    engine = _build_engine()
    assert engine.dialect.name == "sqlite"
    assert engine.dialect.driver == "aiosqlite"


@pytest.mark.parametrize("valores", [{}, {"DB_DRIVER": ""}])
def test_sqlite_sin_driver_usa_aiosqlite(valores):
    database = Database(**valores)
    assert database.url.startswith("sqlite+aiosqlite:///")
