#!/bin/sh

# Salir al primer error
set -e

echo "📦 Aplicando makemigrations..."
pipenv run python manage.py makemigrations core

echo "🛠️ Aplicando migrate..."
pipenv run python manage.py migrate

echo "🚀 Iniciando servidor Django..."
pipenv run python manage.py runserver 0.0.0.0:8000
