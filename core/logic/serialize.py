import json
import logging
from typing import List, Tuple

from core.models import Incident

logger = logging.getLogger(__name__)


def serialize_incidents(incidents=None, json_dump=True):
    incidents = (
        Incident.objects.exclude(latitude=0, longitude=0)
        if incidents is None
        else incidents
    )
    incidents_data = [
        {
            "id": i.id,
            "geometry": i.location.geojson,
            "lat": i.latitude,
            "lon": i.longitude,
            "severity": i.severity,
            "type": i.get_type_display(),
            "date": str(i.incident_date),
            "description": i.description or "Sin descripción",
        }
        for i in incidents
    ]
    logger.info(
        f"Serializando la información de incidentes:\n{incidents_data}"
    )
    return {
        "incidents": incidents,
        "incidents_json": (
            json.dumps(incidents_data) if json_dump else incidents_data
        ),
    }


def build_geojson(
    route_coords: List[Tuple[float, float]], danger_level: float
) -> dict:
    """
    Construye un objeto GeoJSON para representar la ruta.

    Args:
        route_coords: Lista de coordenadas [lat, lon].
        danger_level: Nivel de peligrosidad de la ruta.

    Returns:
        Objeto GeoJSON con la geometría de la ruta.
    """
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [(lon, lat) for lat, lon in route_coords],
        },
        "properties": {"dangerLevel": danger_level},
    }
