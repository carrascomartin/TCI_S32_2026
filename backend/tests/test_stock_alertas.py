"""Pruebas HTTP de alertas de stock y permisos."""

import sqlite3
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app import create_app
from autenticacion_jwt import crear_token_jwt
from autorizacion_roles import obtener_usuario_actual
from utils import load_config, update_config


def con_rol(app, rol: str) -> None:
    """Simula un usuario con el rol indicado para probar los permisos."""
    app.dependency_overrides[obtener_usuario_actual] = lambda: SimpleNamespace(
        roles=[SimpleNamespace(nombre=rol)]
    )


def test_alertas_umbral_suma_paginacion_y_validacion(tmp_path):
    """Calcula el disponible global y aplica umbral y paginación."""
    ruta = tmp_path / "alertas.sqlite3"
    load_config(reload=True)
    app = create_app(cfg=update_config({"database": {"DB_NAME": ruta.as_posix()}}))
    con_rol(app, "empleado_mantenimiento")
    with TestClient(app) as client:
        with sqlite3.connect(ruta) as db:
            db.execute("INSERT INTO ubicaciones (id, codigo) VALUES (1, 'A'), (2, 'B')")
            db.execute("INSERT INTO repuestos (id, codigo, nombre, stock_minimo, activo) VALUES "
                       "(1, 'IGUAL', 'Igual', 5, 1), (2, 'BAJO', 'Bajo', 3, 1), "
                       "(3, 'ALTO', 'Alto', 5, 1), (4, 'VACIO', 'Vacio', 0, 1), "
                       "(5, 'INACTIVO', 'Inactivo', 1, 0)")
            db.execute("INSERT INTO repuestos_x_ubicaciones "
                       "(repuesto_id, ubicacion_id, cantidad_fisica, cantidad_reservada) VALUES "
                       "(1, 1, 5, 2), (1, 2, 2, 0), (2, 1, 4, 2), (3, 1, 6, 0)")
        respuesta = client.get('/api/v0/stock/alertas')
        assert respuesta.status_code == 200, respuesta.text
        pagina = respuesta.json()
        assert (pagina['total'], pagina['offset'], pagina['limit']) == (4, 0, 50)
        assert [(a['repuesto']['codigo'], a['stock_disponible'], a['stock_minimo']) for a in pagina['items']] == [
            ('IGUAL', 5, 5), ('BAJO', 2, 3), ('VACIO', 0, 0), ('INACTIVO', 0, 1)
        ]
        segunda = client.get('/api/v0/stock/alertas?offset=1&limit=2').json()
        assert segunda['total'] == 4
        assert [a['repuesto']['codigo'] for a in segunda['items']] == ['BAJO', 'VACIO']
        assert client.get('/api/v0/stock/alertas?offset=99').json()['items'] == []
        for parametros in ('offset=-1', 'limit=0', 'limit=101'):
            assert client.get('/api/v0/stock/alertas?' + parametros).status_code == 422
        for rol in ('encargado_mantenimiento', 'gerencia_administracion'):
            con_rol(app, rol)
            assert client.get('/api/v0/stock/alertas').status_code == 200
        con_rol(app, 'operario_maquina')
        assert client.get('/api/v0/stock/alertas').status_code == 403


def test_alertas_exigen_token_y_rol_vigente(tmp_path):
    """Exige autenticación y consulta los roles actuales en la base."""
    ruta = tmp_path / 'seguridad.sqlite3'
    configuracion = load_config(reload=True)
    jwt = configuracion.auth.JWT.model_copy(update={'HABILITADO': True})
    configuracion = update_config({
        'database': {'DB_NAME': ruta.as_posix()},
        'auth': configuracion.auth.model_copy(update={'JWT': jwt}),
        'secrets': {'CLAVE_JWT': 'x' * 64},
    })
    app = create_app(cfg=configuracion)
    with TestClient(app) as client:
        assert client.get('/api/v0/stock/alertas').status_code == 401
        with sqlite3.connect(ruta) as db:
            db.execute("INSERT INTO usuarios (id, nombre, apellido, genero, correo, hash_contrasena, verificado) "
                       "VALUES (1, 'Ernesto', 'Demo', 'M', 'empleado@example.invalid', 'hash', 0)")
            db.execute("INSERT INTO roles (id, nombre) VALUES (1, 'empleado_mantenimiento')")
            db.execute('INSERT INTO usuarios_x_roles (usuario_id, rol_id) VALUES (1, 1)')
        token, _ = crear_token_jwt(configuracion, 1, roles=['empleado_mantenimiento'])
        headers = {'Authorization': f'Bearer {token}'}
        assert client.get('/api/v0/stock/alertas', headers=headers).json() == {
            'items': [], 'total': 0, 'offset': 0, 'limit': 50
        }
        with sqlite3.connect(ruta) as db:
            db.execute('DELETE FROM usuarios_x_roles')
        assert client.get('/api/v0/stock/alertas', headers=headers).status_code == 403
