
from typing import Optional

from repositories.incidencias_repository import RepositorioIncidencias
from db.db_models.incidencias import IncidenciaDb
from models.incidencia_mdl import (
    IncidenciaResponseDto,
    MaquinaIncidenciaDto,
    FotoIncidenciaDto,
)


class ServicioIncidencias:
    def __init__(self, repositorio: RepositorioIncidencias):
        self.repositorio = repositorio

    async def serializar(self, incidencia: IncidenciaDb) -> IncidenciaResponseDto:
        maquina = await self.repositorio.obtener_maquina_por_id(
            incidencia.maquina_id
        )

        fotos = await self.repositorio.obtener_fotos_por_incidencia(
            incidencia.id
        )

        datos = {
            "id": incidencia.id,
            "maquina_id": incidencia.maquina_id,
            "maquina": (
                MaquinaIncidenciaDto.model_validate(
                    maquina, from_attributes=True
                )
                if maquina else None
            ),
            "reportada_por_usuario_id": incidencia.reportada_por_usuario_id,
            "descripcion": incidencia.descripcion,
            "estado": incidencia.estado,
            "turno": incidencia.turno,
            "reportada_en": incidencia.reportada_en,
            "resuelta_en": incidencia.resuelta_en,
            "fotos": [
                FotoIncidenciaDto.model_validate(
                    foto, from_attributes=True
                )
                for foto in fotos
            ],
        }

        return IncidenciaResponseDto.model_validate(datos)

    async def listar_incidencias(
        self, offset: int, limit: int, estado: Optional[str]
    ):
        items, total = await self.repositorio.listar(
            offset, limit, estado
        )

        items_serializados = [
            await self.serializar(item) for item in items
        ]

        return {
            "items": items_serializados,
            "total": total,
            "offset": offset,
            "limit": limit,
        }
