"""El arranque ignora Keycloak y conserva la protección JWT local."""
import builtins

import pytest


@pytest.mark.parametrize("habilitado", [False, True])
def test_keycloak_ignorado_sin_dependencia(monkeypatch, tmp_path, habilitado):
    importar = builtins.__import__

    def importar_sin_keycloak(nombre, *args, **kwargs):
        if nombre == "fastapi_keycloak_middleware" or nombre.startswith("fastapi_keycloak_middleware."):
            raise ModuleNotFoundError("Dependencia Keycloak ausente")
        return importar(nombre, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", importar_sin_keycloak)
    monkeypatch.setenv("AUTOCONFIG_SECRETS__CLAVE_JWT", "secreto-de-prueba-para-jwt-local-123456789")
    from app import create_app, register_base_routes
    from utils import load_config, update_config

    cfg = load_config(reload=True)
    keycloak = cfg.auth.KEYCLOAK.model_copy(update={"ENABLED": habilitado})
    jwt = cfg.auth.JWT.model_copy(update={"HABILITADO": True})
    auth = cfg.auth.model_copy(update={"KEYCLOAK": keycloak, "JWT": jwt})
    cfg = update_config({"auth": auth, "database": {"DB_NAME": (tmp_path / "test.sqlite3").as_posix()}})
    app = create_app(cfg=cfg)
    register_base_routes(app)
    from autenticacion_middleware import AutenticacionJWTMiddleware

    assert any(m.cls is AutenticacionJWTMiddleware for m in app.user_middleware)
    assert any(route.path == "/auth/token" for route in app.routes)
