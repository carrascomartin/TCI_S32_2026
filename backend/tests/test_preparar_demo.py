"""Integration coverage for repeatable demo provisioning."""

import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from gestionar_acceso import aplicacion


def test_preparar_demo_es_repetible(tmp_path):
    config = tmp_path / "config.toml"
    original = Path("config.toml").read_text(encoding="utf-8")
    config.write_text(
        original.replace('DB_NAME = "data/db.sqlite3"', f'DB_NAME = "{(tmp_path / "demo.sqlite3").as_posix()}"'),
        encoding="utf-8",
    )
    runner = CliRunner()
    passwords = "".join("Prueba1234\nPrueba1234\n" for _ in range(4))
    first = runner.invoke(aplicacion, ["preparar-demo", "--config", str(config)], input=passwords)
    assert first.exit_code == 0, first.output
    assert "Prueba1234" not in first.output
    second = runner.invoke(aplicacion, ["preparar-demo", "--config", str(config)])
    assert second.exit_code == 0, second.output
    with sqlite3.connect(tmp_path / "demo.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM usuarios").fetchone()[0] == 4
        assert db.execute("SELECT count(*) FROM roles").fetchone()[0] == 4
        assert db.execute("SELECT count(*) FROM usuarios_x_roles").fetchone()[0] == 4
