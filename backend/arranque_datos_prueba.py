"""Punto de entrada del comando de datos de prueba."""

from pathlib import Path
import sys


def ejecutar() -> None:
    # El atajo editable debe encontrar módulos añadidos al backend tras su instalación.
    directorio = str(Path(__file__).resolve().parent)
    if directorio not in sys.path:
        sys.path.insert(0, directorio)
    from datos_prueba import aplicacion

    aplicacion()
