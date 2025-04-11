#!/bin/bash
set -e

# Limpiar versiones anteriores
rm -rf dist/ build/ *.egg-info

# Crear los paquetes
python setup.py sdist bdist_wheel

# Subir a PyPI con el token desde variable de entorno de tu sistema
# Ejemplo de como poder crear tu propia variable de sistema  en la terminal poner lo siguiente:
# export PYPI_TOKEN=pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  -> y con esto tenemos ya tu variable con tu token de pypi
twine upload dist/* -u __token__ -p "$PYPI_TOKEN"
