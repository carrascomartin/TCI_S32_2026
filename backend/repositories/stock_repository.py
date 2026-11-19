"""Consultas de persistencia de existencias y alertas de stock."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db_models.catalogo import RepuestoDb, RepuestoXUbicacionDb


class RepositorioStock:
    """Accede a las existencias mediante la sesión de la solicitud."""

    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def listar_alertas(self, offset: int, limit: int):
        """Devuelve una página y el total de repuestos con disponible bajo el umbral."""
        disponible = func.coalesce(
            func.sum(
                RepuestoXUbicacionDb.cantidad_fisica
                - RepuestoXUbicacionDb.cantidad_reservada
            ),
            0,
        ).label("stock_disponible")
        alertas = (
            select(
                RepuestoDb.id, RepuestoDb.codigo, RepuestoDb.nombre,
                RepuestoDb.stock_minimo, disponible,
            )
            .outerjoin(RepuestoXUbicacionDb, RepuestoDb.id == RepuestoXUbicacionDb.repuesto_id)
            .group_by(RepuestoDb.id, RepuestoDb.codigo, RepuestoDb.nombre, RepuestoDb.stock_minimo)
            .having(disponible <= RepuestoDb.stock_minimo)
            .subquery()
        )
        total = (await self.sesion.execute(select(func.count()).select_from(alertas))).scalar_one()
        consulta = select(alertas).order_by(alertas.c.id).offset(offset).limit(limit)
        items = (await self.sesion.execute(consulta)).all()
        return items, total
