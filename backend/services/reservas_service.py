"""Operaciones de reservas de stock según la máquina de estados de Reserva (T02).

Una reserva nace activa y termina ejecutada (RN-10) o liberada (RN-05). Cada cambio
de existencias se hace con una sentencia condicionada en la base y queda registrado
como movimiento de stock.
"""

from datetime import UTC

from db.db_models.fechas import fecha_actual
from db.db_models.reservas import ItemReservaDb, ReservaDb
from db.db_models.stock import MovimientoStockDb
from models.reserva_mdl import ReservaResponseDto
from repositories.reservas_repository import RepositorioReservas

ACTIVA, EJECUTADA, LIBERADA = "activa", "ejecutada", "liberada"


class ErrorReserva(Exception):
    """Rechazo de una operación con el código HTTP y el código de error del contrato."""

    def __init__(self, codigo_http: int, codigo: str, mensaje: str):
        super().__init__(mensaje)
        self.codigo_http = codigo_http
        self.codigo = codigo
        self.mensaje = mensaje


class ServicioReservas:
    """Coordina la creación, consulta, liberación y ejecución de reservas."""

    def __init__(self, repositorio: RepositorioReservas):
        self.repositorio = repositorio

    async def serializar(self, reservas: list[ReservaDb]) -> list[ReservaResponseDto]:
        """Anida a cada reserva sus partidas con el repuesto y la ubicación."""
        items = await self.repositorio.items_por_reserva([reserva.id for reserva in reservas])
        return [
            ReservaResponseDto.model_validate(
                {
                    **reserva.model_dump(),
                    "items": [
                        {**item.model_dump(), "repuesto": repuesto, "ubicacion": ubicacion}
                        for item, repuesto, ubicacion in items[reserva.id]
                    ],
                }
            )
            for reserva in reservas
        ]

    async def listar(self, desplazamiento: int, limite: int, estado: str | None):
        reservas, total = await self.repositorio.listar(desplazamiento, limite, estado)
        return {
            "items": await self.serializar(reservas),
            "total": total,
            "offset": desplazamiento,
            "limit": limite,
        }

    def _movimiento(self, item: ItemReservaDb, tipo: str, cantidad: int, usuario_id: int, motivo: str,
                    variacion_fisica: int, variacion_reservada: int) -> MovimientoStockDb:
        return MovimientoStockDb(
            repuesto_id=item.repuesto_id,
            ubicacion_id=item.ubicacion_id,
            tipo_movimiento=tipo,
            cantidad=cantidad,
            variacion_fisica=variacion_fisica,
            variacion_reservada=variacion_reservada,
            realizado_por_usuario_id=usuario_id,
            motivo=motivo,
            item_reserva_id=item.id,
        )

    async def crear(self, datos: dict, usuario_id: int) -> ReservaResponseDto:
        """Aparta el stock de cada partida; si alguna no tiene disponible suficiente, no se reserva nada."""
        partidas = datos["items"]
        claves = [(partida["repuesto_id"], partida["ubicacion_id"]) for partida in partidas]
        if len(set(claves)) != len(claves):
            raise ErrorReserva(422, "partida_duplicada", "Hay partidas repetidas para el mismo repuesto y ubicación.")
        for partida in partidas:
            if await self.repositorio.obtener_repuesto(partida["repuesto_id"]) is None:
                raise ErrorReserva(404, "repuesto_inexistente", "Repuesto inexistente.")
            if await self.repositorio.obtener_ubicacion(partida["ubicacion_id"]) is None:
                raise ErrorReserva(404, "ubicacion_inexistente", "Ubicación inexistente.")

        planificada_para = datos["planificada_para"]
        if planificada_para.tzinfo is None:
            planificada_para = planificada_para.replace(tzinfo=UTC)
        reserva = await self.repositorio.guardar(
            ReservaDb(
                creada_por_usuario_id=usuario_id,
                titulo=datos["titulo"],
                motivo=datos["motivo"],
                planificada_para=planificada_para,
                estado=ACTIVA,
            )
        )
        for partida in partidas:
            if not await self.repositorio.reservar(partida["repuesto_id"], partida["ubicacion_id"], partida["cantidad"]):
                raise ErrorReserva(
                    409,
                    "stock_insuficiente",
                    "No hay stock disponible suficiente para reservar una de las partidas.",
                )
            item = await self.repositorio.guardar(ItemReservaDb(reserva_id=reserva.id, **partida))
            await self.repositorio.guardar(
                self._movimiento(item, "reserva", item.cantidad, usuario_id, f"Reserva {reserva.id}: {reserva.titulo}.",
                                 variacion_fisica=0, variacion_reservada=item.cantidad)
            )
        return (await self.serializar([reserva]))[0]

    def _exigir_activa(self, reserva: ReservaDb) -> None:
        if reserva.estado != ACTIVA:
            raise ErrorReserva(409, "reserva_no_activa", f"La reserva está {reserva.estado}; solo se opera sobre reservas activas.")

    async def _liberar_pendiente(self, item: ItemReservaDb, usuario_id: int, motivo: str) -> None:
        """Devuelve al disponible lo reservado que no se consumió."""
        pendiente = item.cantidad - item.cantidad_consumida
        if pendiente == 0:
            return
        if not await self.repositorio.liberar(item.repuesto_id, item.ubicacion_id, pendiente):
            raise ErrorReserva(409, "existencia_inconsistente", "La existencia no tiene reservada la cantidad de la partida.")
        await self.repositorio.guardar(
            self._movimiento(item, "liberacion", pendiente, usuario_id, motivo,
                             variacion_fisica=0, variacion_reservada=-pendiente)
        )

    async def liberar(self, reserva: ReservaDb, usuario_id: int) -> ReservaResponseDto:
        """RN-05: el encargado autoriza la liberación y el stock vuelve a estar disponible."""
        self._exigir_activa(reserva)
        items = (await self.repositorio.items_por_reserva([reserva.id]))[reserva.id]
        for item, _, _ in items:
            await self._liberar_pendiente(item, usuario_id, f"Liberación de la reserva {reserva.id}.")
        reserva.estado = LIBERADA
        reserva.autorizada_por_usuario_id = usuario_id
        reserva.liberada_por_usuario_id = usuario_id
        reserva.liberada_en = fecha_actual()
        reserva = await self.repositorio.guardar(reserva)
        return (await self.serializar([reserva]))[0]

    async def ejecutar(self, reserva: ReservaDb, consumos: list[dict], usuario_id: int) -> ReservaResponseDto:
        """RN-10: descuenta lo consumido del stock físico y libera el resto, todo en la misma transacción."""
        self._exigir_activa(reserva)
        items = {item.id: item for item, _, _ in (await self.repositorio.items_por_reserva([reserva.id]))[reserva.id]}
        por_item: dict[int, int] = {}
        for consumo in consumos:
            item_id = consumo["item_reserva_id"]
            if item_id in por_item:
                raise ErrorReserva(422, "partida_duplicada", "Una partida aparece más de una vez.")
            if item_id not in items:
                raise ErrorReserva(404, "partida_inexistente", "La partida no pertenece a esta reserva.")
            item = items[item_id]
            if consumo["cantidad_consumida"] > item.cantidad - item.cantidad_consumida:
                raise ErrorReserva(409, "consumo_excedido", "Se consume más de lo reservado en una partida.")
            por_item[item_id] = consumo["cantidad_consumida"]

        motivo = f"Ejecución de la reserva {reserva.id}."
        for item in items.values():
            consumida = por_item.get(item.id, 0)
            if consumida:
                if not await self.repositorio.consumir(item.repuesto_id, item.ubicacion_id, consumida):
                    raise ErrorReserva(409, "existencia_inconsistente", "La existencia no alcanza para descontar lo consumido.")
                item.cantidad_consumida += consumida
                await self.repositorio.guardar(item)
                await self.repositorio.guardar(
                    self._movimiento(item, "consumo", consumida, usuario_id, motivo,
                                     variacion_fisica=-consumida, variacion_reservada=-consumida)
                )
            await self._liberar_pendiente(item, usuario_id, motivo)
        reserva.estado = EJECUTADA
        reserva.ejecutada_en = fecha_actual()
        reserva = await self.repositorio.guardar(reserva)
        return (await self.serializar([reserva]))[0]
