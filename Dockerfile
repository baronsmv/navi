# Imagen oficial de Python como base
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Dependencias de sistema (PostGIS y otras)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgis \
    libspatialindex-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia de dependencias de Python al contenedor
COPY requirements.txt .

# Instalación de dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt
