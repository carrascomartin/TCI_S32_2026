"""Operaciones del catálogo de repuestos y de las ubicaciones del almacén."""

from db.db_models.catalogo import RepuestoDb
from db.db_models.fechas import fecha_actual
from models.catalogo_mdl import RepuestoResponseDto
from repositories.repuestos_repository import RepositorioRepuestos


class ServicioRepuestos:
    """Coordina las consultas y modificaciones de repuestos y ubicaciones."""

    def __init__(self, repositorio: RepositorioRepuestos):
        self.repositorio = repositorio

    async def serializar(self, repuestos: list[RepuestoDb]) -> list[RepuestoResponseDto]:
        """Agrega a cada repuesto sus existencias por ubicación; los totales los calcula el DTO."""
        stock = await self.repositorio.stock_por_repuesto([repuesto.id for repuesto in repuestos])
        return [
            RepuestoResponseDto.model_validate(
                {
                    **repuesto.model_dump(),
                    "stock": [
                        {
                            "ubicacion_id": existencia.ubicacion_id,
                            "ubicacion": ubicacion,
                            "cantidad_fisica": existencia.cantidad_fisica,
                            "cantidad_reservada": existencia.cantidad_reservada,
                        }
                        for existencia, ubicacion in stock[repuesto.id]
                    ],
                }
            )
            for repuesto in repuestos
        ]

    async def listar(self, desplazamiento: int, limite: int, buscar: str | None):
        repuestos, total = await self.repositorio.listar_repuestos(desplazamiento, limite, buscar)
        return {
            "items": await self.serializar(repuestos),
            "total": total,
            "offset": desplazamiento,
            "limit": limite,
        }

    async def crear(self, datos: dict) -> RepuestoResponseDto:
        """Incorpora el repuesto sin existencias: el stock entra por recepciones de compra."""
        repuesto = await self.repositorio.guardar(RepuestoDb(**datos))
        return (await self.serializar([repuesto]))[0]

    async def actualizar(self, repuesto: RepuestoDb, cambios: dict) -> RepuestoResponseDto:
        """Aplica los campos enviados y actualiza la fecha de modificación."""
        for campo, valor in cambios.items():
            setattr(repuesto, campo, valor)
        repuesto.actualizado_en = fecha_actual()
        repuesto = await self.repositorio.guardar(repuesto)
        return (await self.serializar([repuesto]))[0]
