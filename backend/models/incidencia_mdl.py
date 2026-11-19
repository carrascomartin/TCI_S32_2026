from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class FotoIncidenciaCreateDto(BaseModel):
    contenido_base64: str
    nombre_archivo: Optional[str] = None
    tipo_mime: str
    capturada_en: Optional[datetime] = None


class FotoIncidenciaDto(BaseModel):
    id: int
    nombre_archivo: Optional[str] = None
    tipo_mime: str
    capturada_en: Optional[datetime] = None
    contenido_base64: str

    class Config:
        from_attributes = True


class IncidenciaCreateDto(BaseModel):
    maquina_codigo: str = Field(max_length=100, min_length=1)
    descripcion: str = Field(min_length=1)
    turno: str
    fotos: Optional[List[FotoIncidenciaCreateDto]] = []


class MaquinaIncidenciaDto(BaseModel):
    id: int
    codigo: str


class IncidenciaResponseDto(BaseModel):
    id: int
    maquina_id: int
    maquina: Optional[MaquinaIncidenciaDto] = None
    reportada_por_usuario_id: int
    descripcion: str
    estado: str
    turno: str
    reportada_en: datetime
    resuelta_en: Optional[datetime] = None
    fotos: List[FotoIncidenciaDto] = []

    class Config:
        from_attributes = True
