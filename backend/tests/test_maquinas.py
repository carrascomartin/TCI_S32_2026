"""Pruebas HTTP del catálogo con base y tokens locales."""

import sqlite3
from types import SimpleNamespace
from fastapi.testclient import TestClient
from app import create_app
from autenticacion_jwt import crear_token_jwt
from autorizacion_roles import obtener_usuario_actual
from utils import load_config, update_config


def test_catalogo_y_roles(tmp_path):
    load_config()
    cfg = update_config({"database": {"DB_NAME": (tmp_path / "catalogo.sqlite3").as_posix()}})
    app = create_app(cfg=cfg)
    app.dependency_overrides[obtener_usuario_actual] = lambda: SimpleNamespace(
        roles=[SimpleNamespace(nombre="encargado_mantenimiento")]
    )
    with TestClient(app) as client:
        tipo = client.post("/api/v0/tipos-maquina", json={"nombre": "Prensa"})
        assert tipo.status_code == 201
        datos = {"codigo": "MAQ-1", "tipo_maquina_id": tipo.json()["id"]}
        assert client.post("/api/v0/maquinas", json=datos).status_code == 201
        assert client.get("/api/v0/maquinas").json()["total"] == 1
        assert client.get("/api/v0/maquinas/1").json()["tipo_maquina"]["nombre"] == "Prensa"
        assert client.patch("/api/v0/maquinas/1", json={"estado": "inactiva"}).status_code == 200
        assert client.post("/api/v0/maquinas", json=datos).status_code == 409
        app.dependency_overrides[obtener_usuario_actual] = lambda: SimpleNamespace(
            roles=[SimpleNamespace(nombre="operario_maquina")]
        )
        assert client.get("/api/v0/maquinas").status_code == 403


def test_token_roles_persistencia_y_errores(tmp_path):
    """El token autentica y los permisos se consultan en cada solicitud."""
    ruta = tmp_path / "seguridad.sqlite3"
    configuracion = load_config(reload=True)
    jwt = configuracion.auth.JWT.model_copy(update={"HABILITADO": True})
    auth = configuracion.auth.model_copy(update={"JWT": jwt})
    configuracion = update_config({
        "database": {"DB_NAME": ruta.as_posix()},
        "auth": auth,
        "secrets": {"CLAVE_JWT": "x" * 64},
    })
    aplicacion = create_app(cfg=configuracion)
    with TestClient(aplicacion) as cliente:
        assert cliente.get("/api/v0/maquinas").status_code == 401
        with sqlite3.connect(ruta) as conexion:
            conexion.execute(
                "INSERT INTO usuarios (id, nombre, apellido, genero, correo, hash_contrasena, verificado) VALUES (1, 'Ana', 'Demo', 'X', 'ana@example.invalid', 'hash', 0)"
            )
            conexion.execute(
                "INSERT INTO roles (id, nombre) VALUES (1, 'encargado_mantenimiento')"
            )
            conexion.execute(
                "INSERT INTO usuarios_x_roles (usuario_id, rol_id) VALUES (1, 1)"
            )
        token, _ = crear_token_jwt(configuracion, 1, roles=["encargado_mantenimiento"])
        cabecera = {"Authorization": f"Bearer {token}"}
        tipo = cliente.post("/api/v0/tipos-maquina", headers=cabecera, json={"nombre": "Prensa"})
        assert tipo.status_code == 201
        maquina = cliente.post(
            "/api/v0/maquinas", headers=cabecera,
            json={"codigo": "M1", "tipo_maquina_id": tipo.json()["id"], "fecha_instalacion": "2026-01-01T12:00:00"},
        )
        assert maquina.status_code == 201, maquina.text
        duplicado = cliente.post(
            "/api/v0/maquinas", headers=cabecera,
            json={"codigo": "M1", "tipo_maquina_id": tipo.json()["id"]},
        )
        assert duplicado.status_code == 409
        assert duplicado.json()["codigo"] == "duplicado"
        assert cliente.get("/api/v0/maquinas?limit=1", headers=cabecera).json()["total"] == 1
        assert cliente.get("/api/v0/maquinas/999", headers=cabecera).status_code == 404
        with sqlite3.connect(ruta) as conexion:
            conexion.execute("DELETE FROM usuarios_x_roles")
        assert cliente.get("/api/v0/maquinas", headers=cabecera).status_code == 403
