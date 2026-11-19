"""Cobertura de la base de prueba que carga datos_prueba.py."""

import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from autenticacion_jwt import verificar_contrasena
from datos_prueba import aplicacion as datos_prueba
from gestionar_acceso import aplicacion as gestionar_acceso


def _configurar(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "prueba.sqlite3"
    config = tmp_path / "config.toml"
    original = Path("config.toml").read_text(encoding="utf-8")
    config.write_text(
        original.replace('DB_NAME = "data/db.sqlite3"', f'DB_NAME = "{base.as_posix()}"'),
        encoding="utf-8",
    )
    return config, base


def _cargar(config: Path, *extra: str, entrada: str | None = None):
    return CliRunner().invoke(
        datos_prueba, ["cargar", "--config", str(config), *extra], input=entrada
    )


def test_carga_datos_coherentes(tmp_path):
    config, base = _configurar(tmp_path)

    resultado = _cargar(config, "--contrasena", "Prueba1234")

    assert resultado.exit_code == 0, resultado.output
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT count(*) FROM maquinas").fetchone()[0] == 9
        assert db.execute("SELECT count(*) FROM repuestos").fetchone()[0] == 10
        # El stock de cada ubicación es la suma de sus movimientos (RN-06).
        descuadrados = db.execute(
            """
            SELECT x.repuesto_id FROM repuestos_x_ubicaciones x
            LEFT JOIN movimientos_stock m
              ON m.repuesto_id = x.repuesto_id AND m.ubicacion_id = x.ubicacion_id
            GROUP BY x.repuesto_id, x.ubicacion_id
            HAVING x.cantidad_fisica != coalesce(sum(m.variacion_fisica), 0)
                OR x.cantidad_reservada != coalesce(sum(m.variacion_reservada), 0)
            """
        ).fetchall()
        assert descuadrados == []
        reservado = db.execute("SELECT sum(cantidad_reservada) FROM repuestos_x_ubicaciones").fetchone()[0]
        en_reservas = db.execute("SELECT sum(cantidad - cantidad_consumida) FROM items_reserva").fetchone()[0]
        assert reservado == en_reservas
        # Hay repuestos en alerta (RN-02) y repuestos con stock suficiente.
        disponibles = db.execute(
            """
            SELECT sum(x.cantidad_fisica - x.cantidad_reservada) <= r.stock_minimo
            FROM repuestos r JOIN repuestos_x_ubicaciones x ON x.repuesto_id = r.id
            GROUP BY r.id
            """
        ).fetchall()
        assert {en_alerta for (en_alerta,) in disponibles} == {0, 1}
        estados_pedido = {estado for (estado,) in db.execute("SELECT estado FROM pedidos_compra")}
        assert estados_pedido == {
            "creado", "pendiente_revision", "pendiente_aprobacion", "confirmado",
            "cancelado", "pendiente_recepcion", "recibido",
        }
        roles = {rol for (rol,) in db.execute("SELECT nombre FROM roles")}
        assert roles == {
            "operario_maquina", "empleado_mantenimiento",
            "encargado_mantenimiento", "gerencia_administracion",
        }
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_no_duplica_y_reinicia_sin_tocar_usuarios(tmp_path):
    config, base = _configurar(tmp_path)
    assert _cargar(config, "--contrasena", "Prueba1234").exit_code == 0
    with sqlite3.connect(base) as db:
        db.execute(
            "INSERT INTO incidencias (maquina_id, reportada_por_usuario_id, descripcion, estado, turno)"
            " VALUES (1, 1, 'agregada a mano', 'reportada', 'tarde')"
        )

    repetida = _cargar(config)
    assert repetida.exit_code == 0, repetida.output
    assert "no se cargó nada" in repetida.output
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT count(*) FROM maquinas").fetchone()[0] == 9
        assert db.execute("SELECT count(*) FROM incidencias").fetchone()[0] == 8

    reiniciada = _cargar(config, "--reiniciar", "--si")
    assert reiniciada.exit_code == 0, reiniciada.output
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT count(*) FROM maquinas").fetchone()[0] == 9
        assert db.execute("SELECT count(*) FROM incidencias WHERE descripcion = 'agregada a mano'").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM usuarios").fetchone()[0] == 5
        hash_operario = db.execute(
            "SELECT hash_contrasena FROM usuarios WHERE correo = 'operario@demo.invalid'"
        ).fetchone()[0]
    assert verificar_contrasena("Prueba1234", hash_operario)


def test_reutiliza_los_usuarios_de_preparar_demo(tmp_path):
    config, base = _configurar(tmp_path)
    contrasenas = "".join("Original1234\nOriginal1234\n" for _ in range(4))
    demo = CliRunner().invoke(
        gestionar_acceso, ["preparar-demo", "--config", str(config)], input=contrasenas
    )
    assert demo.exit_code == 0, demo.output

    # Solo falta el segundo operario, así que pide una única contraseña.
    resultado = _cargar(config, entrada="Prueba1234\nPrueba1234\n")

    assert resultado.exit_code == 0, resultado.output
    with sqlite3.connect(base) as db:
        assert db.execute("SELECT count(*) FROM usuarios").fetchone()[0] == 5
        hash_encargado = db.execute(
            "SELECT hash_contrasena FROM usuarios WHERE correo = 'encargado@demo.invalid'"
        ).fetchone()[0]
    assert verificar_contrasena("Original1234", hash_encargado)
