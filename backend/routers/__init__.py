from .auth_router import router as auth_router
from .autenticacion_router import router as autenticacion_router
from .base_router import base_router
from .maquinas_router import router as maquinas_router
from .repuestos_router import router as repuestos_router

routers = [base_router, auth_router, autenticacion_router, maquinas_router, repuestos_router]
__all__ = ["routers"]
