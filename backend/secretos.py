"""Reglas de las claves secretas y los mensajes que explican cómo configurarlas.

Las claves no se versionan: se leen de variables de entorno (ver README, "Claves y
variables de entorno"). Este módulo concentra el largo mínimo y el texto de ayuda para
que el arranque y la validación del JWT expliquen lo mismo.
"""

from __future__ import annotations

from config import Config

LARGO_MINIMO_BYTES = 32

COMANDO_GENERAR = 'python3 -c "import secrets; print(secrets.token_urlsafe(48))"'


class SecretoInvalidoError(ValueError):
    """Una clave secreta falta o no cumple el largo mínimo."""


def variable_de_entorno(clave: str) -> str:
    """Nombre de la variable de entorno que define ``secrets.<clave>``."""

    return f"AUTOCONFIG_SECRETS__{clave}"


def como_definir(clave: str, largo_minimo: int = LARGO_MINIMO_BYTES) -> str:
    """Indica dónde se define una clave y cómo generar un valor válido."""

    return (
        f"Definila con la variable de entorno {variable_de_entorno(clave)} "
        f"(con Docker, en el archivo .env: copiá .env.example y completalo). "
        f"Necesita al menos {largo_minimo} bytes; para generar una: {COMANDO_GENERAR}"
    )


def validar_secretos(configuracion: Config) -> None:
    """Exige que ``SECRET_KEY`` esté definida y tenga el largo mínimo.

    ``CLAVE_JWT`` se valida aparte, con el largo que pide el algoritmo elegido, y solo
    cuando el JWT local está habilitado (ver ``autenticacion_jwt``).
    """

    valor = configuracion.secrets.SECRET_KEY
    if not valor.strip():
        raise SecretoInvalidoError(f"Falta configurar SECRET_KEY. {como_definir('SECRET_KEY')}")

    largo = len(valor.encode("utf-8"))
    if largo < LARGO_MINIMO_BYTES:
        raise SecretoInvalidoError(
            f"SECRET_KEY tiene {largo} bytes y se exigen al menos {LARGO_MINIMO_BYTES}. "
            f"{como_definir('SECRET_KEY')}"
        )
