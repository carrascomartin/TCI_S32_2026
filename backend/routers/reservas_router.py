"""Endpoints de reservas de stock según el contrato v0."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from autorizacion_roles import requiere_rol
from db.database import get_db
from models.common_mdl import PaginaResponseDto
from models.reserva_mdl import EjecutarReservaDto, ReservaCreateDto, ReservaResponseDto
from repositories.reservas_repository import RepositorioReservas
from services.reservas_service import ErrorReserva, ServicioReservas

router = APIRouter(prefix="/api/v0", tags=["Reservas"])
# Permisos acordados en docs/actores.md: solo el encargado libera una reserva (RN-05).
lectura = requiere_rol(
    "empleado_mantenimiento", "encargado_mantenimiento", "gerencia_administracion"
)
gestion = requiere_rol("empleado_mantenimiento", "encargado_mantenimiento")
liberacion = requiere_rol("encargado_mantenimiento")


def obtener_servicio(sesion: AsyncSession = Depends(get_db)) -> ServicioReservas:
    """Construye el servicio con la sesión de la solicitud."""
    return ServicioReservas(RepositorioReservas(sesion))


def error(codigo_http: int, codigo: str, mensaje: str) -> JSONResponse:
    """Construye la respuesta de error declarada en el contrato."""
    return JSONResponse(status_code=codigo_http, content={"codigo": codigo, "mensaje": mensaje})


async def rechazar(servicio: ServicioReservas, rechazo: ErrorReserva) -> JSONResponse:
    """Deshace los cambios parciales de la operación antes de responder el error."""
    await servicio.repositorio.sesion.rollback()
    return error(rechazo.codigo_http, rechazo.codigo, rechazo.mensaje)


def reserva_inexistente() -> JSONResponse:
    return error(404, "reserva_inexistente", "Reserva inexistente.")


@router.get("/reservas", response_model=PaginaResponseDto[ReservaResponseDto])
async def listar_reservas(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    estado: str | None = Query(None, description="Filtra los resultados por estado actual."),
    usuario=Depends(lectura),
    servicio: ServicioReservas = Depends(obtener_servicio),
):
    """Lista reservas paginadas, las más próximas a ejecutarse primero."""
    return await servicio.listar(offset, limit, estado)


@router.post("/reservas", status_code=201, response_model=ReservaResponseDto)
async def crear_reserva(
    datos: ReservaCreateDto,
    usuario=Depends(gestion),
    servicio: ServicioReservas = Depends(obtener_servicio),
):
    """Crea una reserva activa y aparta el stock de cada partida."""
    try:
        return await servicio.crear(datos.model_dump(), usuario.id)
    except ErrorReserva as rechazo:
        return await rechazar(servicio, rechazo)


@router.get("/reservas/{reserva_id}", response_model=ReservaResponseDto)
async def obtener_reserva(
    reserva_id: int,
    usuario=Depends(lectura),
    servicio: ServicioReservas = Depends(obtener_servicio),
):
    """Obtiene una reserva con sus partidas y cantidades consumidas."""
    reserva = await servicio.repositorio.obtener_reserva(reserva_id)
    if reserva is None:
        return reserva_inexistente()
    return (await servicio.serializar([reserva]))[0]


@router.post("/reservas/{reserva_id}/liberacion", response_model=ReservaResponseDto)
async def liberar_reserva(
    reserva_id: int,
    usuario=Depends(liberacion),
    servicio: ServicioReservas = Depends(obtener_servicio),
):
    """Libera lo reservado y no consumido. Requiere rol encargado (RN-05)."""
    reserva = await servicio.repositorio.obtener_reserva(reserva_id)
    if reserva is None:
        return reserva_inexistente()
    try:
        return await servicio.liberar(reserva, usuario.id)
    except ErrorReserva as rechazo:
        return await rechazar(servicio, rechazo)


@router.post("/reservas/{reserva_id}/ejecucion", response_model=ReservaResponseDto)
async def ejecutar_reserva(
    reserva_id: int,
    datos: EjecutarReservaDto,
    usuario=Depends(gestion),
    servicio: ServicioReservas = Depends(obtener_servicio),
):
    """Descuenta lo consumido del stock físico y libera el resto en una sola transacción (RN-10)."""
    reserva = await servicio.repositorio.obtener_reserva(reserva_id)
    if reserva is None:
        return reserva_inexistente()
    try:
        return await servicio.ejecutar(reserva, datos.model_dump()["items"], usuario.id)
    except ErrorReserva as rechazo:
        return await rechazar(servicio, rechazo)
