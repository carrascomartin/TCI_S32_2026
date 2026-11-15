"""Endpoints del catálogo de máquinas según el contrato v0."""

from datetime import UTC

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from autorizacion_roles import requiere_rol
from db.database import get_db
from db.db_models.catalogo import MaquinaDb, TipoMaquinaDb
from models.catalogo_mdl import (
    MaquinaCreateDto,
    MaquinaResponseDto,
    MaquinaUpdateDto,
    TipoMaquinaCreateDto,
    TipoMaquinaResponseDto,
)
from models.common_mdl import PaginaResponseDto
from repositories.maquinas_repository import RepositorioMaquinas
from services.maquinas_service import ServicioMaquinas

router = APIRouter(prefix="/api/v0", tags=["Máquinas"])
lectura = requiere_rol(
    "empleado_mantenimiento", "encargado_mantenimiento", "gerencia_administracion"
)
escritura = requiere_rol("encargado_mantenimiento")


def obtener_servicio(sesion: AsyncSession = Depends(get_db)) -> ServicioMaquinas:
    """Construye el servicio con la sesión de la solicitud."""
    return ServicioMaquinas(RepositorioMaquinas(sesion))


def error(codigo_http: int, codigo: str, mensaje: str) -> JSONResponse:
    """Construye la respuesta de error declarada en el contrato."""
    return JSONResponse(status_code=codigo_http, content={"codigo": codigo, "mensaje": mensaje})


def normalizar_fecha(datos: dict) -> None:
    """Interpreta como UTC las fechas de instalación sin zona horaria."""
    fecha = datos.get("fecha_instalacion")
    if fecha is not None and fecha.tzinfo is None:
        datos["fecha_instalacion"] = fecha.replace(tzinfo=UTC)


@router.get("/maquinas", response_model=PaginaResponseDto[MaquinaResponseDto])
async def listar_maquinas(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    usuario=Depends(lectura),
    servicio: ServicioMaquinas = Depends(obtener_servicio),
):
    """Lista máquinas paginadas."""
    return await servicio.listar_maquinas(offset, limit)


@router.get("/maquinas/{maquina_id}", response_model=MaquinaResponseDto)
async def obtener_maquina(
    maquina_id: int,
    usuario=Depends(lectura),
    servicio: ServicioMaquinas = Depends(obtener_servicio),
):
    """Consulta el detalle de una máquina."""
    maquina = await servicio.repositorio.obtener(MaquinaDb, maquina_id)
    if maquina is None:
        return error(404, "maquina_inexistente", "Máquina inexistente.")
    return await servicio.serializar(maquina)


@router.post("/maquinas", status_code=201, response_model=MaquinaResponseDto)
async def crear_maquina(
    datos: MaquinaCreateDto,
    usuario=Depends(escritura),
    servicio: ServicioMaquinas = Depends(obtener_servicio),
):
    """Crea una máquina con un tipo existente."""
    if await servicio.repositorio.obtener(TipoMaquinaDb, datos.tipo_maquina_id) is None:
        return error(404, "tipo_inexistente", "Tipo de máquina inexistente.")
    valores = datos.model_dump()
    normalizar_fecha(valores)
    try:
        maquina = await servicio.repositorio.guardar(MaquinaDb(**valores))
    except IntegrityError:
        await servicio.repositorio.sesion.rollback()
        return error(409, "duplicado", "Código o número de serie duplicado.")
    return await servicio.serializar(maquina)


@router.patch("/maquinas/{maquina_id}", response_model=MaquinaResponseDto)
async def actualizar_maquina(
    maquina_id: int,
    datos: MaquinaUpdateDto,
    usuario=Depends(escritura),
    servicio: ServicioMaquinas = Depends(obtener_servicio),
):
    """Actualiza los campos enviados de una máquina."""
    maquina = await servicio.repositorio.obtener(MaquinaDb, maquina_id)
    if maquina is None:
        return error(404, "maquina_inexistente", "Máquina inexistente.")
    cambios = datos.model_dump(exclude_unset=True)
    for campo in ("codigo", "tipo_maquina_id", "estado"):
        if campo in cambios and cambios[campo] is None:
            return error(422, "valor_invalido", f"{campo} no puede ser nulo.")
    if "tipo_maquina_id" in cambios:
        if await servicio.repositorio.obtener(TipoMaquinaDb, cambios["tipo_maquina_id"]) is None:
            return error(404, "tipo_inexistente", "Tipo de máquina inexistente.")
    normalizar_fecha(cambios)
    try:
        return await servicio.serializar(await servicio.actualizar(maquina, cambios))
    except IntegrityError:
        await servicio.repositorio.sesion.rollback()
        return error(409, "duplicado", "Código o número de serie duplicado.")


@router.get("/tipos-maquina", response_model=PaginaResponseDto[TipoMaquinaResponseDto])
async def listar_tipos(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    usuario=Depends(lectura),
    servicio: ServicioMaquinas = Depends(obtener_servicio),
):
    """Lista tipos de máquina paginados."""
    items, total = await servicio.repositorio.listar(TipoMaquinaDb, offset, limit)
    return {"items": items, "total": total, "offset": offset, "limit": limit}


@router.post("/tipos-maquina", status_code=201, response_model=TipoMaquinaResponseDto)
async def crear_tipo(
    datos: TipoMaquinaCreateDto,
    usuario=Depends(escritura),
    servicio: ServicioMaquinas = Depends(obtener_servicio),
):
    """Registra un tipo de máquina."""
    try:
        return await servicio.repositorio.guardar(TipoMaquinaDb(**datos.model_dump()))
    except IntegrityError:
        await servicio.repositorio.sesion.rollback()
        return error(409, "duplicado", "Tipo de máquina duplicado.")
