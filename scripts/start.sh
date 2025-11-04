#!/bin/sh

echo "[START] Aplicando makemigrations..."
python manage.py makemigrations

echo "[START] Aplicando migrate..."
python manage.py migrate

echo "[START] Iniciando servidor Django..."
python manage.py runserver 0.0.0.0:8000
