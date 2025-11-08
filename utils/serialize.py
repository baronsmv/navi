import json
import logging

from core.models import Incident

logger = logging.getLogger(__name__)


def incidents(incidents=None, json_dump=True):
    incidents = (
        Incident.objects.exclude(latitude=0, longitude=0)
        if incidents is None
        else incidents
    )
    incidents_data = [
        {
            "lat": i.latitude,
            "lon": i.longitude,
            "severity": i.severity,
            "type": i.get_type_display(),
            "date": str(i.incident_date),
            "description": i.description or "Sin descripción",
        }
        for i in incidents
    ]
    logger.info(f"Serializando la información de incidentes:\n{incidents_data}")
    return {
        "incidents": incidents,
        "incidents_json": json.dumps(incidents_data) if json_dump else incidents_data,
    }
