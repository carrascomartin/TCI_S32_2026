"""Consultas de persistencia de repuestos, sus existencias y ubicaciones."""

from collections import defaultdict

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db_models.catalogo import RepuestoDb, RepuestoXUbicacionDb, UbicacionDb


class RepositorioRepuestos:
    """Accede a repuestos y ubicaciones mediante la sesión de la solicitud."""

    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def listar_repuestos(self, desplazamiento: int, limite: int, buscar: str | None):
        """Devuelve una página de repuestos, opcionalmente filtrada por nombre, descripción o código."""
        filtro = []
        if buscar and buscar.strip():
            patron = f"%{buscar.strip()}%"
            filtro.append(
                or_(
                    RepuestoDb.nombre.ilike(patron),
                    RepuestoDb.descripcion.ilike(patron),
                    RepuestoDb.codigo.ilike(patron),
                )
            )
        total = await self.sesion.scalar(select(func.count()).select_from(RepuestoDb).where(*filtro))
        consulta = (
            select(RepuestoDb).where(*filtro).order_by(RepuestoDb.id).offset(desplazamiento).limit(limite)
        )
        return list(await self.sesion.scalars(consulta)), total

    async def obtener_repuesto(self, repuesto_id: int):
        return await self.sesion.get(RepuestoDb, repuesto_id)

    async def obtener_repuesto_por_codigo(self, codigo: str):
        return await self.sesion.scalar(select(RepuestoDb).where(RepuestoDb.codigo == codigo))

    async def stock_por_repuesto(self, repuesto_ids: list[int]):
        """Agrupa las existencias por repuesto, con la ubicación de cada una."""
        stock = defaultdict(list)
        if not repuesto_ids:
            return stock
        consulta = (
            select(RepuestoXUbicacionDb, UbicacionDb)
            .join(UbicacionDb, UbicacionDb.id == RepuestoXUbicacionDb.ubicacion_id)
            .where(RepuestoXUbicacionDb.repuesto_id.in_(repuesto_ids))
            .order_by(UbicacionDb.codigo)
        )
        for existencia, ubicacion in (await self.sesion.execute(consulta)).all():
            stock[existencia.repuesto_id].append((existencia, ubicacion))
        return stock

    async def listar_ubicaciones(self, desplazamiento: int, limite: int):
        total = await self.sesion.scalar(select(func.count()).select_from(UbicacionDb))
        consulta = select(UbicacionDb).order_by(UbicacionDb.codigo).offset(desplazamiento).limit(limite)
        return list(await self.sesion.scalars(consulta)), total

    async def guardar(self, entidad):
        """Persiste los cambios dentro de la transacción de la solicitud."""
        self.sesion.add(entidad)
        await self.sesion.flush()
        await self.sesion.refresh(entidad)
        return entidad
