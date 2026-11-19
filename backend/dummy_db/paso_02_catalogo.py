"""Paso 2: cargar tipos, máquinas, ubicaciones y repuestos."""
from datetime import datetime, timedelta, timezone
from db.db_models import TipoMaquinaDb, MaquinaDb, UbicacionDb, RepuestoDb, TipoMaquinaXRepuestoDb

def _fecha(anio: int, mes: int, dia: int) -> datetime:
    return datetime(anio, mes, dia, 12, tzinfo=timezone.utc)

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
    ("C-03", "Caldera", "CA-2021-003", "operativa", _fecha(2021, 2, 10)),
    ("F-04", "Fraccionador", "FR-2024-004", "operativa", _fecha(2024, 1, 15)),
    ("B-05", "Banda transportadora", "BT-2022-005", "operativa", _fecha(2022, 6, 3)),
    ("P-04", "Prensa hidráulica", "PH-2020-004", "operativa", _fecha(2020, 4, 7)),
    ("M-06", "Mezcladora industrial", "MI-2022-006", "operativa", _fecha(2022, 9, 12)),
    ("E-07", "Elevador de carga", "EC-2024-007", "operativa", _fecha(2024, 3, 22)),
    ("C-04", "Caldera", "CA-2022-004", "operativa", _fecha(2022, 10, 8)),
    ("P-05", "Prensa hidráulica", "PH-2023-005", "detenida", _fecha(2023, 5, 19)),
    ("M-07", "Mezcladora industrial", "MI-2024-007", "operativa", _fecha(2024, 4, 16)),
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
    ("REP-00301", "Manómetro de presión", "Instrumento de control de presión.", 2,
     ("Caldera", "Prensa hidráulica"), "A-01-02", 4),
    ("REP-00302", "Sello hidráulico", "Sello para cilindro de la prensa.", 4,
     ("Prensa hidráulica",), "B-01-04", 6),
    ("REP-00303", "Acople de agitador", "Acople del eje de la mezcladora.", 2,
     ("Mezcladora industrial",), "C-01-01", 3),
)



async def cargar(sesion, ahora):
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

    return {"tipos": tipos, "maquinas": maquinas, "ubicaciones": ubicaciones, "repuestos": repuestos}
