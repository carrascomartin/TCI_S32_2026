"""Consultas de stock para el contrato v0."""

from repositories.stock_repository import RepositorioStock


class ServicioStock:
    """Coordina las consultas de stock."""

    def __init__(self, repositorio: RepositorioStock):
        self.repositorio = repositorio

    async def listar_alertas(self, offset: int, limit: int):
        """Devuelve las alertas paginadas con el formato del contrato."""
        filas, total = await self.repositorio.listar_alertas(offset, limit)
        return {
            "items": [
                {
                    "repuesto": {"id": fila.id, "codigo": fila.codigo, "nombre": fila.nombre},
                    "stock_disponible": fila.stock_disponible,
                    "stock_minimo": fila.stock_minimo,
                }
                for fila in filas
            ],
            "total": total,
            "offset": offset,
            "limit": limit,
        }
