"""Operaciones del catálogo de máquinas."""

from db.db_models.catalogo import MaquinaDb, TipoMaquinaDb
from db.db_models.fechas import fecha_actual
from models.catalogo_mdl import MaquinaResponseDto
from repositories.maquinas_repository import RepositorioMaquinas


class ServicioMaquinas:
    """Coordina las consultas y modificaciones del catálogo."""

    def __init__(self, repositorio: RepositorioMaquinas):
        self.repositorio = repositorio

    async def serializar(self, maquina: MaquinaDb):
        """Incluye el tipo de máquina exigido por el contrato v0."""
        tipo = await self.repositorio.obtener(TipoMaquinaDb, maquina.tipo_maquina_id)
        datos = maquina.model_dump()
        datos["tipo_maquina"] = tipo
        return MaquinaResponseDto.model_validate(datos)

    async def listar_maquinas(self, desplazamiento: int, limite: int):
        """Devuelve máquinas paginadas con su tipo."""
        maquinas, total = await self.repositorio.listar(MaquinaDb, desplazamiento, limite)
        return {
            "items": [await self.serializar(maquina) for maquina in maquinas],
            "total": total,
            "offset": desplazamiento,
            "limit": limite,
        }

    async def actualizar(self, maquina: MaquinaDb, cambios: dict):
        """Aplica los campos enviados y actualiza la fecha de modificación."""
        for campo, valor in cambios.items():
            setattr(maquina, campo, valor)
        maquina.actualizado_en = fecha_actual()
        return await self.repositorio.guardar(maquina)
