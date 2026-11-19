"""Endpoints de gestión y reporte de incidencias."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from autorizacion_roles import requiere_rol
from db.database import get_db
from db.db_models.incidencias import IncidenciaDb
from models.incidencia_mdl import IncidenciaCreateDto, IncidenciaResponseDto
from models.common_mdl import PaginaResponseDto
from repositories.incidencias_repository import RepositorioIncidencias
from services.incidencias_service import ServicioIncidencias

router = APIRouter(prefix="/api/v0", tags=["Incidencias"])

rol_reporte = requiere_rol("operario_maquina", "encargado_mantenimiento")
rol_lectura = requiere_rol("empleado_mantenimiento", "encargado_mantenimiento", "gerencia_administracion", "operario_maquina")

def obtener_servicio(sesion: AsyncSession = Depends(get_db)) -> ServicioIncidencias:
    return ServicioIncidencias(RepositorioIncidencias(sesion))

def error(codigo_http: int, codigo: str, mensaje: str) -> JSONResponse:
    return JSONResponse(status_code=codigo_http, content={"codigo": codigo, "mensaje": mensaje})

@router.post("/incidencias", status_code=201, response_model=IncidenciaResponseDto)
async def reportar_incidencia(
    datos: IncidenciaCreateDto,
    usuario=Depends(rol_reporte),
    servicio: ServicioIncidencias = Depends(obtener_servicio),
):
    """Registra una incidencia sobre una máquina e incluye fotos opcionales."""
    maquina = await servicio.repositorio.obtener_maquina_por_codigo(datos.maquina_codigo)
    if not maquina:
        return error(404, "maquina_inexistente", f"La máquina con código {datos.maquina_codigo} no existe.")

    turnos_validos = ["manana", "tarde", "noche"]
    if datos.turno not in turnos_validos:
        return error(422, "turno_invalido", "El turno especificado no es válido.")

    nueva_incidencia = IncidenciaDb(
        maquina_id=maquina.id,
        reportada_por_usuario_id=usuario.id,
        descripcion=datos.descripcion,
        turno=datos.turno,
        estado="reportada"
    )

    incidencia_guardada = await servicio.repositorio.guardar(nueva_incidencia, datos.fotos or [])
    return await servicio.serializar(incidencia_guardada)

@router.get("/incidencias", response_model=PaginaResponseDto[IncidenciaResponseDto])
async def listar_incidencias(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: Optional[str] = None,
    usuario=Depends(rol_lectura),
    servicio: ServicioIncidencias = Depends(obtener_servicio),
):
    """Lista incidencias de forma paginada y permite filtrar por estado."""
    return await servicio.listar_incidencias(offset, limit, estado)

@router.get("/incidencias/{incidencia_id}", response_model=IncidenciaResponseDto)
async def obtener_incidencia(
    incidencia_id: int,
    usuario=Depends(rol_lectura),
    servicio: ServicioIncidencias = Depends(obtener_servicio),
):
    """Obtiene el detalle y evidencia de una incidencia específica."""
    incidencia = await servicio.repositorio.obtener(IncidenciaDb, incidencia_id)
    if not incidencia:
        return error(404, "incidencia_inexistente", "La incidencia consultada no existe.")
    return await servicio.serializar(incidencia)