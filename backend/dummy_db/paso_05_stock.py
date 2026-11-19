"""Paso 5: reservas, movimientos y existencias finales."""
from datetime import timedelta
from db.db_models import ReservaDb, ItemReservaDb, MovimientoStockDb, RepuestoXUbicacionDb
from .paso_02_catalogo import REPUESTOS

# (título, motivo, planificada para dentro de, creada hace, items [(repuesto, ubicación, cantidad)])
RESERVAS = (
    ("Mantenimiento preventivo de fraccionadores",
     "Cambio programado de juntas y control de sensores.", timedelta(days=3), timedelta(days=2),
     (("REP-00031", "C-02-11", 4), ("REP-00106", "B-04-02", 2))),
    ("Mantenimiento de prensa hidráulica",
     "Inspección del circuito y reemplazo preventivo del sello.", timedelta(days=5), timedelta(days=1),
     (("REP-00302", "B-01-04", 2), ("REP-00301", "A-01-02", 1))),
    ("Revisión de mezcladora",
     "Reserva del acople para una parada programada.", timedelta(days=7), timedelta(hours=12),
     (("REP-00303", "C-01-01", 1),)),
)



async def cargar(sesion, contexto):
    ahora, usuarios = contexto["ahora"], contexto["usuarios"]
    repuestos, ubicaciones, fisico, reservado, movimientos = (contexto[k] for k in ("repuestos", "ubicaciones", "fisico", "reservado", "movimientos"))
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

