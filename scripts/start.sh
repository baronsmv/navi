#!/bin/sh

if [ ! -f .env ] && [ -f .env.copy ]; then
    echo "[START] Copiando archivo de entorno por defecto..."
    cp .env.copy .env
fi

if [ ! -f config.yaml ] && [ -f config.yaml.copy ]; then
    echo "[START] Copiando archivo de configuración por defecto..."
    cp .env.copy .env
fi

echo "[START] Precargando grafos..."
python -m utils.prebuild_graphs

echo "[START] Copiando archivos estáticos al servidor..."
python manage.py collectstatic --noinput

echo "[START] Aplicando makemigrations..."
python manage.py makemigrations

echo "[START] Aplicando migrate..."
python manage.py migrate

echo "[START] Iniciando servidor Django..."
gunicorn --bind 0.0.0.0:8000 navi.wsgi:application
