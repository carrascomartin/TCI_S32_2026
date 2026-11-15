"""Consultas de persistencia del catálogo de máquinas."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class RepositorioMaquinas:
    """Accede a las máquinas y tipos mediante la sesión de la solicitud."""

    def __init__(self, sesion: AsyncSession):
        self.sesion = sesion

    async def listar(self, modelo, desplazamiento: int, limite: int):
        """Devuelve una página y la cantidad total de registros."""
        total = await self.sesion.scalar(select(func.count()).select_from(modelo))
        consulta = select(modelo).order_by(modelo.id).offset(desplazamiento).limit(limite)
        registros = await self.sesion.scalars(consulta)
        return list(registros), total

    async def obtener(self, modelo, identificador: int):
        """Busca un registro por su identificador."""
        return await self.sesion.get(modelo, identificador)

    async def guardar(self, entidad):
        """Persiste los cambios dentro de la transacción de la solicitud."""
        self.sesion.add(entidad)
        await self.sesion.flush()
        await self.sesion.refresh(entidad)
        return entidad
