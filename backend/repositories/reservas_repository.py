"""Consultas de persistencia de reservas, sus partidas y las existencias que afectan."""

from collections import defaultdict

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.db_models.catalogo import RepuestoDb, RepuestoXUbicacionDb, UbicacionDb
from db.db_models.fechas import fecha_actual
from db.db_models.reservas import ItemReservaDb, ReservaDb


class RepositorioReservas:
    """Accede a reservas y existencias mediante la sesión de la solicitud."""

    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def obtener_reserva(self, reserva_id: int):
        return await self.sesion.get(ReservaDb, reserva_id)

    async def obtener_repuesto(self, repuesto_id: int):
        return await self.sesion.get(RepuestoDb, repuesto_id)

    async def obtener_ubicacion(self, ubicacion_id: int):
        return await self.sesion.get(UbicacionDb, ubicacion_id)

    async def listar(self, desplazamiento: int, limite: int, estado: str | None):
        """Devuelve una página de reservas, las más próximas a ejecutarse primero, y el total."""
        filtro = [ReservaDb.estado == estado] if estado else []
        total = await self.sesion.scalar(select(func.count()).select_from(ReservaDb).where(*filtro))
        consulta = (
            select(ReservaDb)
            .where(*filtro)
            .order_by(ReservaDb.planificada_para, ReservaDb.id)
            .offset(desplazamiento)
            .limit(limite)
        )
        return list(await self.sesion.scalars(consulta)), total

    async def items_por_reserva(self, reserva_ids: list[int]):
        """Agrupa las partidas de cada reserva con su repuesto y su ubicación."""
        items = defaultdict(list)
        if not reserva_ids:
            return items
        consulta = (
            select(ItemReservaDb, RepuestoDb, UbicacionDb)
            .join(RepuestoDb, RepuestoDb.id == ItemReservaDb.repuesto_id)
            .join(UbicacionDb, UbicacionDb.id == ItemReservaDb.ubicacion_id)
            .where(ItemReservaDb.reserva_id.in_(reserva_ids))
            .order_by(ItemReservaDb.id)
        )
        for item, repuesto, ubicacion in (await self.sesion.execute(consulta)).all():
            items[item.reserva_id].append((item, repuesto, ubicacion))
        return items

    async def _ajustar_existencia(self, repuesto_id: int, ubicacion_id: int, condicion, **valores) -> bool:
        """Aplica el cambio solo si la condición se cumple en la base, en una única sentencia."""
        existencia = RepuestoXUbicacionDb
        resultado = await self.sesion.execute(
            update(existencia)
            .where(
                existencia.repuesto_id == repuesto_id,
                existencia.ubicacion_id == ubicacion_id,
                condicion,
            )
            .values(**valores, actualizado_en=fecha_actual())
            .execution_options(synchronize_session=False)
        )
        return resultado.rowcount == 1

    async def reservar(self, repuesto_id: int, ubicacion_id: int, cantidad: int) -> bool:
        """Aparta stock si el disponible (físico menos reservado) alcanza."""
        existencia = RepuestoXUbicacionDb
        return await self._ajustar_existencia(
            repuesto_id,
            ubicacion_id,
            existencia.cantidad_fisica - existencia.cantidad_reservada >= cantidad,
            cantidad_reservada=existencia.cantidad_reservada + cantidad,
        )

    async def liberar(self, repuesto_id: int, ubicacion_id: int, cantidad: int) -> bool:
        existencia = RepuestoXUbicacionDb
        return await self._ajustar_existencia(
            repuesto_id,
            ubicacion_id,
            existencia.cantidad_reservada >= cantidad,
            cantidad_reservada=existencia.cantidad_reservada - cantidad,
        )

    async def consumir(self, repuesto_id: int, ubicacion_id: int, cantidad: int) -> bool:
        """Descuenta lo consumido del stock físico y de lo reservado a la vez."""
        existencia = RepuestoXUbicacionDb
        return await self._ajustar_existencia(
            repuesto_id,
            ubicacion_id,
            (existencia.cantidad_reservada >= cantidad) & (existencia.cantidad_fisica >= cantidad),
            cantidad_fisica=existencia.cantidad_fisica - cantidad,
            cantidad_reservada=existencia.cantidad_reservada - cantidad,
        )

    async def guardar(self, entidad):
        """Persiste los cambios dentro de la transacción de la solicitud."""
        self.sesion.add(entidad)
        await self.sesion.flush()
        await self.sesion.refresh(entidad)
        return entidad
