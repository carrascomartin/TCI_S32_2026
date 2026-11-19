"""Claves de prueba: la configuración las exige y config.toml ya no las trae."""

import os

os.environ.setdefault("AUTOCONFIG_SECRETS__SECRET_KEY", "clave-solo-para-las-pruebas-0123456789")
