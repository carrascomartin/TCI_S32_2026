"""Carga una base de prueba con datos del dominio para probar el backend sin los mocks del frontend.

Los datos siguen los fixtures de ``frontend/public/mock`` (mismas máquinas, ubicaciones y
repuestos), pero coherentes entre sí: el stock de cada ubicación coincide con la suma de
sus movimientos, lo reservado con las reservas activas, y hay incidencias, reparaciones y
pedidos de compra en cada estado.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import typer
from sqlalchemy import delete, func, select

from db.database import dispose_db, get_sessionmaker, init_db
from db.db_models import (
    FotoIncidenciaDb,
    IncidenciaDb,
    InformeResolucionDb,
    ItemPedidoCompraDb,
    ItemRecepcionCompraDb,
    ItemReservaDb,
    MaquinaDb,
    MovimientoStockDb,
    PedidoCompraDb,
    RecepcionCompraDb,
    ReparacionDb,
    RepuestoDb,
    RepuestoXUbicacionDb,
    ReservaDb,
    RolDb,
    TipoMaquinaDb,
    TipoMaquinaXRepuestoDb,
    UbicacionDb,
    UsoRepuestoReparacionDb,
)
from models.autenticacion_mdl import RolCrearDto, UsuarioCrearDto
from services.autenticacion_service import ServicioAutenticacion
from utils import load_config


aplicacion = typer.Typer(help="Carga datos de prueba del dominio en la base configurada.")


@aplicacion.callback()
def principal() -> None:
    """Datos de prueba del dominio."""

# La planta opera en horario de Argentina; el turno se deriva de la hora del reporte.
ZONA_PLANTA = timezone(timedelta(hours=-3))


def _fecha(anio: int, mes: int, dia: int) -> datetime:
    return datetime(anio, mes, dia, 12, tzinfo=timezone.utc)

# (clave, rol, nombre, apellido, género, correo). Los correos coinciden con preparar-demo.
USUARIOS = (
    ("operario", "operario_maquina", "Olivia", "Paz", "F", "operario@demo.invalid"),
    ("operario2", "operario_maquina", "Omar", "Ruiz", "M", "operario2@demo.invalid"),
    ("empleado", "empleado_mantenimiento", "Ernesto", "Díaz", "M", "empleado@demo.invalid"),
    ("encargado", "encargado_mantenimiento", "Elena", "Suárez", "F", "encargado@demo.invalid"),
    ("gerencia", "gerencia_administracion", "Gabriela", "Ortiz", "F", "gerencia@demo.invalid"),
)

TIPOS_MAQUINA = (
    ("Caldera", "Genera vapor para los procesos de esterilización y secado."),
    ("Fraccionador", "Dosifica y fracciona el producto en sus envases."),
    ("Banda transportadora", "Traslada el producto entre estaciones de la línea."),
    ("Prensa hidráulica", "Compacta comprimidos a presión controlada."),
    ("Mezcladora industrial", "Homogeneiza materias primas antes del fraccionado."),
    ("Elevador de carga", "Sube insumos y producto entre plantas."),
)

# (código, tipo, número de serie, estado, fecha de instalación)
MAQUINAS = (
    ("C-01", "Caldera", "CA-2018-001", "operativa", _fecha(2018, 3, 10)),
    ("C-02", "Caldera", "CA-2020-002", "operativa", _fecha(2020, 5, 4)),
    ("F-01", "Fraccionador", "FR-2019-001", "operativa", _fecha(2019, 9, 12)),
    ("F-02", "Fraccionador", "FR-2022-002", "operativa", _fecha(2022, 2, 21)),
    ("F-03", "Fraccionador", "FR-2023-003", "operativa", _fecha(2023, 7, 3)),
    ("B-04", "Banda transportadora", "BT-2020-004", "operativa", _fecha(2020, 11, 30)),
    ("P-03", "Prensa hidráulica", "PH-2021-003", "detenida", _fecha(2021, 6, 15)),
    ("M-05", "Mezcladora industrial", "MI-2019-005", "en_mantenimiento", _fecha(2019, 4, 2)),
    ("E-06", "Elevador de carga", "EC-2023-006", "en_calibracion", _fecha(2023, 8, 20)),
)

UBICACIONES = (
    "A-01-01", "A-01-02", "A-02-08", "A-03-12", "B-01-04",
    "B-02-05", "B-04-02", "C-01-01", "C-02-11", "D-01-05",
)

# (código, nombre, descripción, stock mínimo, tipos compatibles, ubicación, stock físico final)
REPUESTOS = (
    ("REP-00142", "Rodamiento 6205-2RS", "Rodamiento sellado de bolas para ejes de motor.", 5,
     ("Fraccionador", "Banda transportadora"), "A-03-12", 2),
    ("REP-00087", "Filtro de aceite FO-18", "Filtro del circuito de lubricación del quemador.", 6,
     ("Caldera",), "B-01-04", 4),
    ("REP-00203", "Correa dentada HTD-8M", "Correa de transmisión del rodillo motriz.", 3,
     ("Banda transportadora",), "A-02-08", 0),
    ("REP-00031", "Junta tórica NBR 40 mm", "Junta de estanqueidad de la tolva dosificadora.", 8,
     ("Fraccionador",), "C-02-11", 18),
    ("REP-00106", "Sensor de temperatura PT100", "Sonda de temperatura del hogar de la caldera.", 3,
     ("Caldera",), "B-04-02", 7),
    ("REP-00058", "Válvula de seguridad 1/2 in", "Válvula de alivio de sobrepresión.", 4,
     ("Caldera",), "D-01-05", 3),
    ("REP-00215", "Bomba de engranajes BG-20", "Bomba del circuito hidráulico de la prensa.", 1,
     ("Prensa hidráulica",), "A-01-02", 2),
    ("REP-00174", "Motor eléctrico 1,5 kW", "Motor trifásico de accionamiento.", 1,
     ("Mezcladora industrial", "Banda transportadora"), "B-02-05", 1),
    ("REP-00090", "Paleta de mezcla PM-300", "Paleta de acero inoxidable del agitador.", 2,
     ("Mezcladora industrial",), "C-01-01", 5),
    ("REP-00012", "Cable de acero 8 mm (m)", "Cable de tracción del elevador, por metro.", 20,
     ("Elevador de carga",), "A-01-01", 60),
)

# (clave, máquina, reportada por, descripción, estado, hace cuánto se reportó, resuelta hace, con foto)
INCIDENCIAS = (
    ("i1", "F-02", "operario", "Vibración anormal en el motor del fraccionador.",
     "en_triage", timedelta(hours=3), None, False),
    ("i2", "B-04", "operario2", "La banda se desalinea y el producto se corre hacia un costado.",
     "en_reparacion", timedelta(days=1, hours=6), None, False),
    ("i3", "C-01", "operario", "Fuga en la válvula de presión de la caldera.",
     "en_triage", timedelta(hours=10), None, False),
    ("i4", "F-03", "operario2", "Temperatura elevada en el cabezal dosificador.",
     "reportada", timedelta(minutes=40), None, True),
    ("i5", "B-04", "operario", "Se cortó la correa dentada y la banda no arranca.",
     "pendiente_repuesto", timedelta(days=4), None, False),
    ("i6", "C-02", "operario", "La caldera tarda mucho en levantar presión al inicio del turno.",
     "resuelta", timedelta(days=7), timedelta(days=6), False),
    ("i7", "M-05", "operario2", "Ruido metálico en la paleta de mezcla al subir de velocidad.",
     "resuelta", timedelta(days=12), timedelta(days=11), False),
)

# (incidencia, estado, iniciada hace, completada hace, usos [(repuesto, cantidad)], informe)
REPARACIONES = (
    ("i2", "en_curso", timedelta(days=1), None, (("REP-00142", 1),), None),
    ("i5", "pendiente_repuesto", timedelta(days=3, hours=20), None, (), None),
    ("i6", "completada", timedelta(days=6, hours=20), timedelta(days=6), (("REP-00087", 2),),
     "Se reemplazaron los dos filtros de aceite obstruidos y se purgó el circuito."),
    ("i7", "completada", timedelta(days=11, hours=22), timedelta(days=11), (("REP-00090", 1),),
     "Se cambió la paleta de mezcla con desgaste en el borde de ataque."),
)

# (estado, urgencia, origen, creado por, asignado a, revisión resuelta por, motivo,
#  motivo de cancelación, hace cuánto, items [(repuesto, cantidad)],
#  recepciones [(recibida hace, [(repuesto, ubicación, cantidad)])])
PEDIDOS_COMPRA = (
    ("creado", "normal", "manual", "empleado", None, None,
     "Reposición preventiva de filtros.", None, timedelta(hours=2),
     (("REP-00087", 8),), ()),
    ("pendiente_revision", "urgente", "automatico", "empleado", None, None,
     "Stock por debajo del mínimo.", None, timedelta(hours=6),
     (("REP-00142", 12),), ()),
    ("pendiente_aprobacion", "normal", "manual", "empleado", "encargado", None,
     None, None, timedelta(days=1),
     (("REP-00058", 4),), ()),
    ("confirmado", "urgente", "manual", "empleado", "encargado", "encargado",
     "Correa cortada en la banda B-04, línea detenida.", None, timedelta(days=3, hours=22),
     (("REP-00203", 4),), ()),
    ("cancelado", "normal", "manual", "empleado", None, "encargado",
     None, "Pedido duplicado.", timedelta(days=5),
     (("REP-00031", 3),), ()),
    ("pendiente_recepcion", "urgente", "manual", "encargado", "encargado", "encargado",
     None, None, timedelta(days=9),
     (("REP-00215", 2), ("REP-00174", 2)),
     ((timedelta(days=8), (("REP-00174", "B-02-05", 1),)),)),
    ("recibido", "normal", "automatico", "empleado", "encargado", "encargado",
     "Reposición por nivel mínimo.", None, timedelta(days=15),
     (("REP-00106", 5),),
     ((timedelta(days=14), (("REP-00106", "B-04-02", 5),)),)),
)

# (título, motivo, planificada para dentro de, creada hace, items [(repuesto, ubicación, cantidad)])
RESERVAS = (
    ("Mantenimiento preventivo de fraccionadores",
     "Cambio programado de juntas y control de sensores.", timedelta(days=3), timedelta(days=2),
     (("REP-00031", "C-02-11", 4), ("REP-00106", "B-04-02", 2))),
)

# Las tablas del dominio, en orden seguro para borrar con claves foráneas activas.
TABLAS_DOMINIO = (
    MovimientoStockDb,
    ItemReservaDb,
    ReservaDb,
    ItemRecepcionCompraDb,
    RecepcionCompraDb,
    ItemPedidoCompraDb,
    PedidoCompraDb,
    InformeResolucionDb,
    UsoRepuestoReparacionDb,
    ReparacionDb,
    FotoIncidenciaDb,
    IncidenciaDb,
    RepuestoXUbicacionDb,
    TipoMaquinaXRepuestoDb,
    RepuestoDb,
    UbicacionDb,
    MaquinaDb,
    TipoMaquinaDb,
)

# PNG de 1x1 px: alcanza para probar el alta y la lectura de evidencias.
FOTO_PRUEBA = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def turno_de(fecha: datetime) -> str:
    hora = fecha.astimezone(ZONA_PLANTA).hour
    if 6 <= hora < 14:
        return "manana"
    if 14 <= hora < 22:
        return "tarde"
    return "noche"


async def _asegurar_usuarios(
    servicio: ServicioAutenticacion, contrasena: str | None
) -> dict[str, int]:
    """Reutiliza los usuarios existentes y crea los que falten, sin tocar sus contraseñas."""

    roles_existentes = set((await servicio.sesion.scalars(select(RolDb.nombre))).all())
    for rol in {rol for _, rol, *_ in USUARIOS} - roles_existentes:
        await servicio.crear_rol(RolCrearDto(nombre=rol))

    ids = {}
    for clave, rol, nombre, apellido, genero, correo in USUARIOS:
        usuario = await servicio.buscar_usuario_por_correo(correo)
        if usuario is None:
            if contrasena is None:
                contrasena = typer.prompt(
                    "Contraseña para los usuarios de prueba", hide_input=True, confirmation_prompt=True
                )
            usuario = await servicio.crear_usuario(
                UsuarioCrearDto(
                    nombre=nombre,
                    apellido=apellido,
                    genero=genero,
                    correo=correo,
                    contrasena=contrasena,
                    roles=[rol],
                )
            )
        ids[clave] = usuario.id
    return ids


async def _cargar_dominio(sesion, usuarios: dict[str, int]) -> dict[str, int]:
    # Todas las fechas se pasan con zona horaria: SQLModel rechaza las fechas sin zona al guardar.
    ahora = datetime.now(timezone.utc)

    tipos = {nombre: TipoMaquinaDb(nombre=nombre, descripcion=desc) for nombre, desc in TIPOS_MAQUINA}
    sesion.add_all(tipos.values())
    await sesion.flush()

    maquinas = {
        codigo: MaquinaDb(
            codigo=codigo,
            tipo_maquina_id=tipos[tipo].id,
            numero_serie=serie,
            estado=estado,
            fecha_instalacion=instalada,
            creado_en=instalada,
        )
        for codigo, tipo, serie, estado, instalada in MAQUINAS
    }
    ubicaciones = {
        codigo: UbicacionDb(
            codigo=codigo,
            descripcion=f"Estante {codigo[0]}, fila {int(codigo[2:4])}, nivel {int(codigo[5:])}",
        )
        for codigo in UBICACIONES
    }
    repuestos = {
        codigo: RepuestoDb(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            stock_minimo=minimo,
            creado_en=ahora - timedelta(days=60),
        )
        for codigo, nombre, descripcion, minimo, *_ in REPUESTOS
    }
    sesion.add_all([*maquinas.values(), *ubicaciones.values(), *repuestos.values()])
    await sesion.flush()

    for codigo, _, _, _, compatibles, *_ in REPUESTOS:
        sesion.add_all(
            TipoMaquinaXRepuestoDb(tipo_maquina_id=tipos[tipo].id, repuesto_id=repuestos[codigo].id)
            for tipo in compatibles
        )

    ubicacion_de = {codigo: ubicacion for codigo, *_, ubicacion, _ in REPUESTOS}
    # Variaciones de stock por (repuesto, ubicación) que generan los datos, para cuadrar la carga inicial.
    fisico = defaultdict(int)
    reservado = defaultdict(int)
    movimientos: list[MovimientoStockDb] = []

    incidencias = {}
    for clave, maquina, reporto, descripcion, estado, hace, resuelta_hace, con_foto in INCIDENCIAS:
        reportada_en = ahora - hace
        incidencia = IncidenciaDb(
            maquina_id=maquinas[maquina].id,
            reportada_por_usuario_id=usuarios[reporto],
            descripcion=descripcion,
            estado=estado,
            turno=turno_de(reportada_en),
            reportada_en=reportada_en,
            resuelta_en=ahora - resuelta_hace if resuelta_hace else None,
        )
        sesion.add(incidencia)
        incidencias[clave] = incidencia
    await sesion.flush()
    for clave, *_, con_foto in INCIDENCIAS:
        if con_foto:
            sesion.add(
                FotoIncidenciaDb(
                    incidencia_id=incidencias[clave].id,
                    contenido_base64=FOTO_PRUEBA,
                    nombre_archivo="cabezal.png",
                    tipo_mime="image/png",
                    capturada_en=incidencias[clave].reportada_en,
                )
            )

    for clave, estado, iniciada_hace, completada_hace, usos, informe in REPARACIONES:
        reparacion = ReparacionDb(
            incidencia_id=incidencias[clave].id,
            empleado_id=usuarios["empleado"],
            estado=estado,
            iniciada_en=ahora - iniciada_hace,
            completada_en=ahora - completada_hace if completada_hace else None,
        )
        sesion.add(reparacion)
        await sesion.flush()
        for repuesto, cantidad in usos:
            uso = UsoRepuestoReparacionDb(
                reparacion_id=reparacion.id,
                repuesto_id=repuestos[repuesto].id,
                cantidad=cantidad,
                usada_por_usuario_id=usuarios["empleado"],
                usada_en=reparacion.iniciada_en + timedelta(hours=2),
            )
            sesion.add(uso)
            await sesion.flush()
            ubicacion = ubicacion_de[repuesto]
            fisico[repuesto, ubicacion] -= cantidad
            movimientos.append(
                MovimientoStockDb(
                    repuesto_id=repuestos[repuesto].id,
                    ubicacion_id=ubicaciones[ubicacion].id,
                    tipo_movimiento="consumo",
                    cantidad=cantidad,
                    variacion_fisica=-cantidad,
                    variacion_reservada=0,
                    realizado_por_usuario_id=usuarios["empleado"],
                    ocurrido_en=uso.usada_en,
                    motivo=f"Uso en la reparación de la incidencia {incidencias[clave].id}.",
                    uso_repuesto_reparacion_id=uso.id,
                )
            )
        if informe:
            sesion.add(
                InformeResolucionDb(
                    reparacion_id=reparacion.id,
                    empleado_id=usuarios["empleado"],
                    resumen=informe,
                    creada_en=reparacion.completada_en,
                )
            )

    for (
        estado, urgencia, origen, creo, asignado, resolvio, motivo, cancelacion, hace, items, recepciones
    ) in PEDIDOS_COMPRA:
        creado_en = ahora - hace
        pedido = PedidoCompraDb(
            creada_por_usuario_id=usuarios[creo],
            urgencia=urgencia,
            origen=origen,
            estado=estado,
            motivo=motivo,
            asignado_a_usuario_id=usuarios[asignado] if asignado else None,
            revision_resuelta_por_usuario_id=usuarios[resolvio] if resolvio else None,
            revision_resuelta_en=creado_en + timedelta(hours=4) if resolvio else None,
            motivo_cancelacion=cancelacion,
            creado_en=creado_en,
        )
        sesion.add(pedido)
        await sesion.flush()
        lineas = {}
        for repuesto, cantidad in items:
            linea = ItemPedidoCompraDb(
                pedido_compra_id=pedido.id, repuesto_id=repuestos[repuesto].id, cantidad_solicitada=cantidad
            )
            sesion.add(linea)
            lineas[repuesto] = linea
        await sesion.flush()
        for recibida_hace, recibido in recepciones:
            recepcion = RecepcionCompraDb(
                pedido_compra_id=pedido.id,
                recibida_por_usuario_id=usuarios["encargado"],
                recibida_en=ahora - recibida_hace,
            )
            sesion.add(recepcion)
            await sesion.flush()
            for repuesto, ubicacion, cantidad in recibido:
                item = ItemRecepcionCompraDb(
                    recepcion_id=recepcion.id,
                    item_pedido_compra_id=lineas[repuesto].id,
                    ubicacion_id=ubicaciones[ubicacion].id,
                    cantidad=cantidad,
                )
                sesion.add(item)
                await sesion.flush()
                fisico[repuesto, ubicacion] += cantidad
                movimientos.append(
                    MovimientoStockDb(
                        repuesto_id=repuestos[repuesto].id,
                        ubicacion_id=ubicaciones[ubicacion].id,
                        tipo_movimiento="entrada",
                        cantidad=cantidad,
                        variacion_fisica=cantidad,
                        variacion_reservada=0,
                        realizado_por_usuario_id=usuarios["encargado"],
                        ocurrido_en=recepcion.recibida_en,
                        motivo=f"Recepción del pedido de compra {pedido.id}.",
                        item_recepcion_compra_id=item.id,
                    )
                )

    for titulo, motivo, planificada_en, creada_hace, items in RESERVAS:
        reserva = ReservaDb(
            creada_por_usuario_id=usuarios["encargado"],
            titulo=titulo,
            motivo=motivo,
            planificada_para=ahora + planificada_en,
            creada_en=ahora - creada_hace,
        )
        sesion.add(reserva)
        await sesion.flush()
        for repuesto, ubicacion, cantidad in items:
            item = ItemReservaDb(
                reserva_id=reserva.id,
                repuesto_id=repuestos[repuesto].id,
                ubicacion_id=ubicaciones[ubicacion].id,
                cantidad=cantidad,
            )
            sesion.add(item)
            await sesion.flush()
            reservado[repuesto, ubicacion] += cantidad
            movimientos.append(
                MovimientoStockDb(
                    repuesto_id=repuestos[repuesto].id,
                    ubicacion_id=ubicaciones[ubicacion].id,
                    tipo_movimiento="reserva",
                    cantidad=cantidad,
                    variacion_fisica=0,
                    variacion_reservada=cantidad,
                    realizado_por_usuario_id=usuarios["encargado"],
                    ocurrido_en=reserva.creada_en,
                    motivo=f"Reserva para: {titulo}.",
                    item_reserva_id=item.id,
                )
            )

    # La carga inicial completa lo que falta para llegar al stock físico final de cada repuesto.
    for codigo, *_, ubicacion, final in REPUESTOS:
        inicial = final - fisico[codigo, ubicacion]
        if inicial < 0:
            raise ValueError(f"Los datos de {codigo} dejan el stock físico negativo.")
        if inicial > 0:
            movimientos.append(
                MovimientoStockDb(
                    repuesto_id=repuestos[codigo].id,
                    ubicacion_id=ubicaciones[ubicacion].id,
                    tipo_movimiento="entrada",
                    cantidad=inicial,
                    variacion_fisica=inicial,
                    variacion_reservada=0,
                    realizado_por_usuario_id=usuarios["encargado"],
                    ocurrido_en=ahora - timedelta(days=30),
                    motivo="Carga inicial del inventario.",
                )
            )
        sesion.add(
            RepuestoXUbicacionDb(
                repuesto_id=repuestos[codigo].id,
                ubicacion_id=ubicaciones[ubicacion].id,
                cantidad_fisica=final,
                cantidad_reservada=reservado[codigo, ubicacion],
                actualizado_en=ahora,
            )
        )
    sesion.add_all(movimientos)
    await sesion.flush()

    return {
        "máquinas": len(maquinas),
        "ubicaciones": len(ubicaciones),
        "repuestos": len(repuestos),
        "incidencias": len(incidencias),
        "pedidos de compra": len(PEDIDOS_COMPRA),
        "movimientos de stock": len(movimientos),
    }


async def _hay_datos(sesion) -> bool:
    return bool(
        await sesion.scalar(select(func.count()).select_from(MaquinaDb))
        or await sesion.scalar(select(func.count()).select_from(RepuestoDb))
    )


async def _ejecutar(nombre_configuracion: str, contrasena: str | None, reiniciar: bool) -> str:
    load_config(nombre_configuracion, reload=True)
    await init_db()
    try:
        async with get_sessionmaker()() as sesion:
            if reiniciar:
                for tabla in TABLAS_DOMINIO:
                    await sesion.execute(delete(tabla))
            elif await _hay_datos(sesion):
                return "La base ya tiene datos del dominio; no se cargó nada. Usá --reiniciar para recargarlos."
            usuarios = await _asegurar_usuarios(ServicioAutenticacion(sesion), contrasena)
            cantidades = await _cargar_dominio(sesion, usuarios)
            await sesion.commit()
    finally:
        await dispose_db()
    detalle = ", ".join(f"{cantidad} {nombre}" for nombre, cantidad in cantidades.items())
    return f"Datos de prueba cargados: {detalle}."


@aplicacion.command("cargar")
def cargar(
    contrasena: str | None = typer.Option(
        None,
        "--contrasena",
        envvar="TCI_CONTRASENA_PRUEBA",
        help="Contraseña de los usuarios de prueba que haya que crear. Si falta, se pide sin mostrarla.",
    ),
    reiniciar: bool = typer.Option(
        False, "--reiniciar", help="Borra los datos del dominio antes de cargar. No toca usuarios ni roles."
    ),
    sin_confirmar: bool = typer.Option(False, "--si", "-y", help="No pedir confirmación al reiniciar."),
    configuracion: str = typer.Option("default", "--config", help="Entorno TOML."),
) -> None:
    """Carga máquinas, stock, incidencias, reparaciones, compras y reservas de prueba."""

    if reiniciar and not sin_confirmar:
        typer.confirm(
            "Se borran todas las máquinas, repuestos, incidencias, compras y reservas. ¿Continuar?",
            abort=True,
        )
    try:
        typer.echo(asyncio.run(_ejecutar(configuracion, contrasena, reiniciar)))
    except Exception as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    aplicacion()
