
"""Pruebas HTTP para el reporte y consulta de incidencias."""

import sqlite3

from fastapi.testclient import TestClient

from app import create_app
from autenticacion_jwt import crear_token_jwt
from utils import load_config, update_config


def preparar_usuario(ruta):
    """Inserta el usuario y su rol para respetar las claves foráneas."""
    with sqlite3.connect(ruta) as conexion:
        conexion.execute(
            """
            INSERT INTO usuarios
                (id, nombre, apellido, genero, correo, hash_contrasena, verificado)
            VALUES
                (1, 'Ana', 'Demo', 'X', 'ana@example.invalid', 'hash', 0)
            """
        )
        conexion.execute(
            """
            INSERT INTO roles (id, nombre)
            VALUES (1, 'encargado_mantenimiento')
            """
        )
        conexion.execute(
            """
            INSERT INTO usuarios_x_roles (usuario_id, rol_id)
            VALUES (1, 1)
            """
        )


def preparar_configuracion(ruta):
    """Configura SQLite temporal y autenticación JWT."""
    configuracion = load_config(reload=True)

    jwt = configuracion.auth.JWT.model_copy(
        update={"HABILITADO": True}
    )
    auth = configuracion.auth.model_copy(
        update={"JWT": jwt}
    )

    return update_config({
        "database": {"DB_NAME": ruta.as_posix()},
        "auth": auth,
        "secrets": {"CLAVE_JWT": "x" * 64},
    })


def test_reportar_listar_y_obtener_incidencias(tmp_path):
    ruta = tmp_path / "incidencias.sqlite3"
    cfg = preparar_configuracion(ruta)
    app = create_app(cfg=cfg)

    with TestClient(app) as client:
        preparar_usuario(ruta)

        token, _ = crear_token_jwt(
            cfg,
            1,
            roles=["encargado_mantenimiento"],
        )
        cabecera = {"Authorization": f"Bearer {token}"}

        tipo = client.post(
            "/api/v0/tipos-maquina",
            headers=cabecera,
            json={"nombre": "Prensa"},
        )
        assert tipo.status_code == 201, tipo.text

        maquina = client.post(
            "/api/v0/maquinas",
            headers=cabecera,
            json={
                "codigo": "MAQ-1",
                "tipo_maquina_id": tipo.json()["id"],
            },
        )
        assert maquina.status_code == 201, maquina.text

        respuesta = client.post(
            "/api/v0/incidencias",
            headers=cabecera,
            json={
                "maquina_codigo": "MAQ-1",
                "descripcion": "La máquina presenta una vibración anormal.",
                "turno": "manana",
            },
        )
        assert respuesta.status_code == 201, respuesta.text

        incidencia = respuesta.json()

        assert incidencia["maquina_id"] == maquina.json()["id"]
        assert incidencia["maquina"]["codigo"] == "MAQ-1"
        assert incidencia["maquina"]["tipo_maquina"]["nombre"] == "Prensa"
        assert incidencia["descripcion"] == (
            "La máquina presenta una vibración anormal."
        )
        assert incidencia["turno"] == "manana"
        assert incidencia["estado"] == "reportada"

        listado = client.get(
            "/api/v0/incidencias?offset=0&limit=10",
            headers=cabecera,
        )
        assert listado.status_code == 200, listado.text
        assert listado.json()["total"] == 1
        assert listado.json()["offset"] == 0
        assert listado.json()["limit"] == 10
        assert len(listado.json()["items"]) == 1
        assert (
            listado.json()["items"][0]["maquina"]["tipo_maquina"]["nombre"]
            == "Prensa"
        )

        detalle = client.get(
            f"/api/v0/incidencias/{incidencia['id']}",
            headers=cabecera,
        )
        assert detalle.status_code == 200, detalle.text
        assert detalle.json()["id"] == incidencia["id"]

        maquina_inexistente = client.post(
            "/api/v0/incidencias",
            headers=cabecera,
            json={
                "maquina_codigo": "NO-EXISTE",
                "descripcion": "Prueba de máquina inexistente.",
                "turno": "manana",
            },
        )
        assert maquina_inexistente.status_code == 404

        incidencia_inexistente = client.get(
            "/api/v0/incidencias/999",
            headers=cabecera,
        )
        assert incidencia_inexistente.status_code == 404

        turno_invalido = client.post(
            "/api/v0/incidencias",
            headers=cabecera,
            json={
                "maquina_codigo": "MAQ-1",
                "descripcion": "Prueba de turno inválido.",
                "turno": "madrugada",
            },
        )
        assert turno_invalido.status_code == 422

        # Cambia el rol persistido para comprobar la autorización 403.
        with sqlite3.connect(ruta) as conexion:
            conexion.execute("DELETE FROM usuarios_x_roles")
            conexion.execute(
                """
                INSERT INTO roles (id, nombre)
                VALUES (2, 'rol_sin_permiso')
                """
            )
            conexion.execute(
                """
                INSERT INTO usuarios_x_roles (usuario_id, rol_id)
                VALUES (1, 2)
                """
            )

        sin_permisos = client.get(
            "/api/v0/incidencias",
            headers=cabecera,
        )
        assert sin_permisos.status_code == 403


def test_incidencias_requiere_autenticacion(tmp_path):
    ruta = tmp_path / "incidencias_auth.sqlite3"
    cfg = preparar_configuracion(ruta)
    app = create_app(cfg=cfg)

    with TestClient(app) as client:
        sin_token = client.get("/api/v0/incidencias")
        assert sin_token.status_code == 401

        preparar_usuario(ruta)

        token, _ = crear_token_jwt(
            cfg,
            1,
            roles=["encargado_mantenimiento"],
        )

        cabecera = {"Authorization": f"Bearer {token}"}

        respuesta = client.get(
            "/api/v0/incidencias",
            headers=cabecera,
        )
        assert respuesta.status_code == 200, respuesta.text
