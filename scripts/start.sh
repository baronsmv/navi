#!/bin/sh

echo "[START] Precargando grafos..."
python scripts/prebuild_graphs.py

echo "[START] Copiando archivos estáticos al servidor..."
python manage.py collectstatic --noinput

echo "[START] Aplicando makemigrations..."
python manage.py makemigrations

echo "[START] Aplicando migrate..."
python manage.py migrate

echo "[START] Iniciando servidor Django..."
gunicorn --bind 0.0.0.0:8000 navi.wsgi:application
