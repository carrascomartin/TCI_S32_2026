"""Descubre los módulos del backend sin mantener una lista manual."""

from pathlib import Path

from setuptools import setup

modulos = sorted(
    archivo.stem
    for archivo in Path(__file__).resolve().parent.glob("*.py")
    if archivo.stem != "setup" and not archivo.stem.startswith("test_")
)

setup(py_modules=modulos)
