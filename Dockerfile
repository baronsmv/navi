# Usa una imagen oficial de Python como base
FROM python:3.11-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias de sistema para PostGIS y otros requerimientos
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    libpq-dev \
    postgis \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar pipenv
RUN pip install pipenv

COPY Pipfile* ./
RUN pipenv install --dev
COPY . .

# Exponer el puerto en el que se ejecutará Django
EXPOSE 8000

# Comando por defecto para ejecutar el servidor de Django
CMD ["pipenv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
