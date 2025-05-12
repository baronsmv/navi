from datetime import date, time

import pytest
from django.contrib.gis.geos import Point

from core.logic.route_danger import get_nearby_incidents
from core.models import Incident


@pytest.mark.django_db
def test_get_nearby_incidents_within_radius():
    # Crear incidente con ubicación específica
    incident = Incident.objects.create(
        type="homicide",
        description="Ejemplo",
        incident_date=date(2002, 2, 2),
        incident_time=time(12, 0),
        latitude=20.095023172226565,
        longitude=-98.71471166610719,
        location=Point(-98.71471166610719, 20.095023172226565),  # lon, lat
        severity=5,
        status="unresolved",
    )

    # Punto cercano (simula un nodo del grafo)
    node_lat = 20.09505
    node_lon = -98.71470
    radius = 100  # metros

    # Ejecutar función
    results = get_nearby_incidents(node_lat, node_lon, radius)

    # Verificar que se incluye el incidente
    assert len(results) == 1
    assert results[0].id == incident.id
