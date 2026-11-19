"""Pruebas de reservas: RN-05 (reserva y liberación) y RN-10 (consumo en una transacción)."""

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from app import create_app
from datos_prueba import aplicacion as datos_prueba
from utils import load_config, update_config

CONTRASENA = "Prueba1234"


@pytest.fixture
def entorno(tmp_path: Path):
    base = tmp_path / "reservas.sqlite3"
    config = tmp_path / "config.toml"
    config.write_text(
        Path("config.toml")
        .read_text(encoding="utf-8")
        .replace('DB_NAME = "data/db.sqlite3"', f'DB_NAME = "{base.as_posix()}"'),
        encoding="utf-8",
    )
    cargado = CliRunner().invoke(
        datos_prueba, ["cargar", "--config", str(config), "--contrasena", CONTRASENA]
    )
    assert cargado.exit_code == 0, cargado.output
    configuracion = load_config(reload=True)
    jwt = configuracion.auth.JWT.model_copy(update={"HABILITADO": True})
    app = create_app(
        cfg=update_config(
            {
                "database": {"DB_NAME": base.as_posix()},
                "auth": configuracion.auth.model_copy(update={"JWT": jwt}),
                "secrets": {"CLAVE_JWT": "x" * 64},
            }
        )
    )
    with TestClient(app) as client:
        yield client, base
    load_config(reload=True)


def sesion(client: TestClient, correo: str) -> dict:
    respuesta = client.post(
        "/auth/token",
        data={"username": correo, "password": CONTRASENA, "grant_type": "password"},
    )
    assert respuesta.status_code == 200, respuesta.text
    return {"Authorization": f"Bearer {respuesta.json()['access_token']}"}


def existencias_libres(base: Path, minimo: int, cuantas: int) -> list[tuple[int, int, int]]:
    """Existencias con al menos `minimo` unidades disponibles: (repuesto, ubicación, disponible)."""
    with sqlite3.connect(base) as db:
        filas = db.execute(
            "SELECT repuesto_id, ubicacion_id, cantidad_fisica - cantidad_reservada FROM repuestos_x_ubicaciones"
            " WHERE cantidad_fisica - cantidad_reservada >= ? ORDER BY repuesto_id, ubicacion_id",
            (minimo,),
        ).fetchall()
    assert len(filas) >= cuantas
    return filas[:cuantas]


def existencia(base: Path, repuesto_id: int, ubicacion_id: int) -> tuple[int, int]:
    """(físico, reservado) de una existencia."""
    with sqlite3.connect(base) as db:
        return db.execute(
            "SELECT cantidad_fisica, cantidad_reservada FROM repuestos_x_ubicaciones"
            " WHERE repuesto_id = ? AND ubicacion_id = ?",
            (repuesto_id, ubicacion_id),
        ).fetchone()


def movimientos(base: Path, tipo: str) -> int:
    with sqlite3.connect(base) as db:
        return db.execute("SELECT count(*) FROM movimientos_stock WHERE tipo_movimiento = ?", (tipo,)).fetchone()[0]


def nueva(*partidas: tuple[int, int, int]) -> dict:
    return {
        "titulo": "Preventivo de prueba",
        "motivo": "Cambio programado.",
        "planificada_para": "2026-12-01T08:00:00Z",
        "items": [{"repuesto_id": r, "ubicacion_id": u, "cantidad": c} for r, u, c in partidas],
    }


def test_rn05_la_reserva_aparta_stock_y_no_supera_el_disponible(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    (repuesto, ubicacion, disponible), = existencias_libres(base, 2, 1)
    fisico, reservado = existencia(base, repuesto, ubicacion)
    disponible_api = client.get(f"/api/v0/repuestos/{repuesto}", headers=empleado).json()["stock_disponible_total"]

    creada = client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, disponible)))

    assert creada.status_code == 201, creada.text
    cuerpo = creada.json()
    assert cuerpo["estado"] == "activa"
    assert [(i["repuesto"]["id"], i["ubicacion"]["id"], i["cantidad"], i["cantidad_consumida"]) for i in cuerpo["items"]] == [
        (repuesto, ubicacion, disponible, 0)
    ]
    assert existencia(base, repuesto, ubicacion) == (fisico, reservado + disponible)
    assert client.get(f"/api/v0/repuestos/{repuesto}", headers=empleado).json()["stock_disponible_total"] == disponible_api - disponible

    # Lo reservado ya no está disponible: una unidad más se rechaza sin tocar nada.
    reservas_antes, reservas_mov = client.get("/api/v0/reservas", headers=empleado).json()["total"], movimientos(base, "reserva")
    sin_stock = client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, 1)))
    assert (sin_stock.status_code, sin_stock.json()["codigo"]) == (409, "stock_insuficiente")
    assert existencia(base, repuesto, ubicacion) == (fisico, reservado + disponible)
    assert client.get("/api/v0/reservas", headers=empleado).json()["total"] == reservas_antes
    assert movimientos(base, "reserva") == reservas_mov


def test_rn05_si_una_partida_no_alcanza_no_se_reserva_ninguna(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    (r1, u1, _), (r2, u2, d2) = existencias_libres(base, 1, 2)
    antes = existencia(base, r1, u1)

    rechazo = client.post("/api/v0/reservas", headers=empleado, json=nueva((r1, u1, 1), (r2, u2, d2 + 1)))

    assert (rechazo.status_code, rechazo.json()["codigo"]) == (409, "stock_insuficiente")
    assert existencia(base, r1, u1) == antes


def test_rn05_solo_el_encargado_libera_la_reserva(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    encargado = sesion(client, "encargado@demo.invalid")
    (repuesto, ubicacion, _), = existencias_libres(base, 2, 1)
    antes = existencia(base, repuesto, ubicacion)
    reserva = client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, 2))).json()

    assert client.post(f"/api/v0/reservas/{reserva['id']}/liberacion", headers=empleado).status_code == 403
    assert existencia(base, repuesto, ubicacion) == (antes[0], antes[1] + 2)

    liberadas_antes = movimientos(base, "liberacion")
    liberada = client.post(f"/api/v0/reservas/{reserva['id']}/liberacion", headers=encargado)

    assert liberada.status_code == 200, liberada.text
    encargado_id = client.get("/auth/me", headers=encargado).json()["usuario_id"]
    assert liberada.json()["estado"] == "liberada"
    assert liberada.json()["autorizada_por_usuario_id"] == encargado_id
    assert liberada.json()["liberada_en"] is not None
    assert existencia(base, repuesto, ubicacion) == antes
    assert movimientos(base, "liberacion") == liberadas_antes + 1

    # Una reserva liberada ya no se libera ni se ejecuta.
    otra_vez = client.post(f"/api/v0/reservas/{reserva['id']}/liberacion", headers=encargado)
    assert (otra_vez.status_code, otra_vez.json()["codigo"]) == (409, "reserva_no_activa")
    item = reserva["items"][0]["id"]
    ejecutar = client.post(
        f"/api/v0/reservas/{reserva['id']}/ejecucion",
        headers=empleado,
        json={"items": [{"item_reserva_id": item, "cantidad_consumida": 1}]},
    )
    assert (ejecutar.status_code, ejecutar.json()["codigo"]) == (409, "reserva_no_activa")
    assert existencia(base, repuesto, ubicacion) == antes


def test_rn10_ejecutar_descuenta_lo_consumido_y_libera_el_resto(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    (r1, u1, _), (r2, u2, _) = existencias_libres(base, 3, 2)
    antes1, antes2 = existencia(base, r1, u1), existencia(base, r2, u2)
    reserva = client.post("/api/v0/reservas", headers=empleado, json=nueva((r1, u1, 3), (r2, u2, 2))).json()
    item1, item2 = (i["id"] for i in reserva["items"])
    consumos, liberaciones = movimientos(base, "consumo"), movimientos(base, "liberacion")

    # Se usan 2 de las 3 unidades de la primera partida y nada de la segunda.
    ejecutada = client.post(
        f"/api/v0/reservas/{reserva['id']}/ejecucion",
        headers=empleado,
        json={"items": [{"item_reserva_id": item1, "cantidad_consumida": 2}]},
    )

    assert ejecutada.status_code == 200, ejecutada.text
    cuerpo = ejecutada.json()
    assert cuerpo["estado"] == "ejecutada"
    assert cuerpo["ejecutada_en"] is not None
    assert {i["id"]: i["cantidad_consumida"] for i in cuerpo["items"]} == {item1: 2, item2: 0}
    # El físico baja lo consumido y no queda nada reservado por esta reserva.
    assert existencia(base, r1, u1) == (antes1[0] - 2, antes1[1])
    assert existencia(base, r2, u2) == antes2
    assert movimientos(base, "consumo") == consumos + 1
    assert movimientos(base, "liberacion") == liberaciones + 2


def test_rn10_si_falla_el_descuento_no_se_libera_ni_descuenta_nada(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    (r1, u1, _), (r2, u2, _) = existencias_libres(base, 2, 2)
    reserva = client.post("/api/v0/reservas", headers=empleado, json=nueva((r1, u1, 2), (r2, u2, 2))).json()
    item1, item2 = (i["id"] for i in reserva["items"])
    reservada1 = existencia(base, r1, u1)
    consumos = movimientos(base, "consumo")
    # La existencia de la segunda partida desaparece: su descuento va a fallar
    # después de haber descontado la primera.
    with sqlite3.connect(base) as db:
        db.execute("DELETE FROM repuestos_x_ubicaciones WHERE repuesto_id = ? AND ubicacion_id = ?", (r2, u2))

    fallida = client.post(
        f"/api/v0/reservas/{reserva['id']}/ejecucion",
        headers=empleado,
        json={"items": [{"item_reserva_id": item1, "cantidad_consumida": 2}, {"item_reserva_id": item2, "cantidad_consumida": 2}]},
    )

    assert (fallida.status_code, fallida.json()["codigo"]) == (409, "existencia_inconsistente")
    assert existencia(base, r1, u1) == reservada1
    assert movimientos(base, "consumo") == consumos
    detalle = client.get(f"/api/v0/reservas/{reserva['id']}", headers=empleado).json()
    assert detalle["estado"] == "activa"
    assert [i["cantidad_consumida"] for i in detalle["items"]] == [0, 0]


def test_errores_de_reserva(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    (repuesto, ubicacion, _), = existencias_libres(base, 2, 1)

    assert client.post("/api/v0/reservas", headers=empleado, json=nueva((99999, ubicacion, 1))).json()["codigo"] == "repuesto_inexistente"
    assert client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, 99999, 1))).json()["codigo"] == "ubicacion_inexistente"
    duplicada = client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, 1), (repuesto, ubicacion, 1)))
    assert (duplicada.status_code, duplicada.json()["codigo"]) == (422, "partida_duplicada")
    assert client.post("/api/v0/reservas", headers=empleado, json={**nueva((repuesto, ubicacion, 1)), "items": []}).status_code == 422
    assert client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, 0))).status_code == 422
    assert client.get("/api/v0/reservas/99999", headers=empleado).json()["codigo"] == "reserva_inexistente"

    reserva = client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, 2))).json()
    item = reserva["items"][0]["id"]
    ruta = f"/api/v0/reservas/{reserva['id']}/ejecucion"
    excedida = client.post(ruta, headers=empleado, json={"items": [{"item_reserva_id": item, "cantidad_consumida": 3}]})
    assert (excedida.status_code, excedida.json()["codigo"]) == (409, "consumo_excedido")
    ajena = client.post(ruta, headers=empleado, json={"items": [{"item_reserva_id": 99999, "cantidad_consumida": 1}]})
    assert (ajena.status_code, ajena.json()["codigo"]) == (404, "partida_inexistente")
    assert client.get(f"/api/v0/reservas/{reserva['id']}", headers=empleado).json()["estado"] == "activa"


def test_listado_y_permisos(entorno):
    client, base = entorno
    empleado = sesion(client, "empleado@demo.invalid")
    gerencia = sesion(client, "gerencia@demo.invalid")
    operario = sesion(client, "operario@demo.invalid")
    (repuesto, ubicacion, _), = existencias_libres(base, 2, 1)
    reserva = client.post("/api/v0/reservas", headers=empleado, json=nueva((repuesto, ubicacion, 1))).json()
    client.post(f"/api/v0/reservas/{reserva['id']}/liberacion", headers=sesion(client, "encargado@demo.invalid"))

    todas = client.get("/api/v0/reservas?limit=100", headers=gerencia).json()
    assert todas["total"] >= 2
    liberadas = client.get("/api/v0/reservas?estado=liberada", headers=gerencia).json()
    assert [r["id"] for r in liberadas["items"]] == [reserva["id"]]
    activas = client.get("/api/v0/reservas?estado=activa", headers=gerencia).json()
    assert activas["total"] == todas["total"] - 1
    assert len(client.get("/api/v0/reservas?limit=1", headers=gerencia).json()["items"]) == 1

    assert client.get("/api/v0/reservas").status_code == 401
    assert client.post("/api/v0/reservas", json=nueva((repuesto, ubicacion, 1))).status_code == 401
    assert client.get("/api/v0/reservas", headers=operario).status_code == 403
    assert client.post("/api/v0/reservas", headers=gerencia, json=nueva((repuesto, ubicacion, 1))).status_code == 403
    assert client.post("/api/v0/reservas", headers=operario, json=nueva((repuesto, ubicacion, 1))).status_code == 403
