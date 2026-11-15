from .identidad import (
    UsuarioDb,
    RolDb,
    UsuarioXRolDb,
)
from .catalogo import (
    TipoMaquinaDb,
    MaquinaDb,
    UbicacionDb,
    RepuestoDb,
    TipoMaquinaXRepuestoDb,
    RepuestoXUbicacionDb,
)
from .incidencias import (
    IncidenciaDb,
    FotoIncidenciaDb,
    ReparacionDb,
    UsoRepuestoReparacionDb,
    InformeResolucionDb,
)
from .compras import (
    PedidoCompraDb,
    ItemPedidoCompraDb,
    RecepcionCompraDb,
    ItemRecepcionCompraDb,
)
from .reservas import (
    ReservaDb,
    ItemReservaDb,
)
from .stock import (
    MovimientoStockDb,
)

__all__ = [
    "UsuarioDb",
    "RolDb",
    "UsuarioXRolDb",
    "TipoMaquinaDb",
    "MaquinaDb",
    "UbicacionDb",
    "RepuestoDb",
    "TipoMaquinaXRepuestoDb",
    "RepuestoXUbicacionDb",
    "IncidenciaDb",
    "FotoIncidenciaDb",
    "ReparacionDb",
    "UsoRepuestoReparacionDb",
    "InformeResolucionDb",
    "PedidoCompraDb",
    "ItemPedidoCompraDb",
    "RecepcionCompraDb",
    "ItemRecepcionCompraDb",
    "ReservaDb",
    "ItemReservaDb",
    "MovimientoStockDb",
]
