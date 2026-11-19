"""Endpoints de consulta de stock."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from autorizacion_roles import requiere_rol
from db.database import get_db
from models.common_mdl import PaginaResponseDto
from models.stock_mdl import AlertaStockResponseDto
from repositories.stock_repository import RepositorioStock
from services.stock_service import ServicioStock

router = APIRouter(prefix="/api/v0/stock", tags=["Stock"])
lectura = requiere_rol(
    "empleado_mantenimiento", "encargado_mantenimiento", "gerencia_administracion"
)


def obtener_servicio(sesion: AsyncSession = Depends(get_db)) -> ServicioStock:
    """Construye el servicio con la sesión de la solicitud."""
    return ServicioStock(RepositorioStock(sesion))


@router.get(
    "/alertas", summary="Listar alertas de stock",
    response_model=PaginaResponseDto[AlertaStockResponseDto],
)
async def listar_alertas_stock(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    usuario=Depends(lectura),
    servicio: ServicioStock = Depends(obtener_servicio),
):
    """Lista repuestos cuyo stock disponible alcanzó el mínimo configurado."""
    return await servicio.listar_alertas(offset, limit)
