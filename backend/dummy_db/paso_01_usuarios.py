"""Paso 1: crear roles y usuarios de prueba."""
from sqlalchemy import select
from db.db_models import RolDb
from models.autenticacion_mdl import RolCrearDto, UsuarioCrearDto
from services.autenticacion_service import ServicioAutenticacion

# Contraseña común exclusivamente para las cuentas de prueba recién creadas.
CONTRASENA_DUMMY = "test"

# (clave, rol, nombre, apellido, género, correo). Los correos coinciden con preparar-demo.
USUARIOS = (
    ("operario", "operario_maquina", "Olivia", "Paz", "F", "operario@test"),
    ("operario2", "operario_maquina", "Omar", "Ruiz", "M", "operario2@test"),
    ("empleado", "empleado_mantenimiento", "Ernesto", "Díaz", "M", "empleado@test"),
    ("encargado", "encargado_mantenimiento", "Elena", "Suárez", "F", "encargado@test"),
    ("gerencia", "gerencia_administracion", "Gabriela", "Ortiz", "F", "gerencia@test"),
)



async def _asegurar_usuarios(servicio: ServicioAutenticacion) -> dict[str, int]:
    """Reutiliza los usuarios existentes y crea los que falten, sin tocar sus contraseñas."""

    roles_existentes = set((await servicio.sesion.scalars(select(RolDb.nombre))).all())
    for rol in {rol for _, rol, *_ in USUARIOS} - roles_existentes:
        await servicio.crear_rol(RolCrearDto(nombre=rol))

    ids = {}
    for clave, rol, nombre, apellido, genero, correo in USUARIOS:
        usuario = await servicio.buscar_usuario_por_correo(correo)
        if usuario is None:
            # Solo las credenciales fijas de esta base dummy omiten el mínimo de 8 caracteres.
            usuario = await servicio.crear_usuario(
                UsuarioCrearDto.model_construct(
                    nombre=nombre,
                    apellido=apellido,
                    genero=genero,
                    correo=correo,
                    contrasena=CONTRASENA_DUMMY,
                    roles=[rol],
                )
            )
        elif rol not in {asignado.nombre for asignado in usuario.roles}:
            raise ValueError(f"El usuario existente {correo} no tiene el rol esperado: {rol}.")
        ids[clave] = usuario.id
    return ids


