import logging
from typing import Tuple, Dict

import networkx as nx
from django.contrib.gis.geos import Polygon, Point
from django.contrib.gis.measure import D
from django.db.models import QuerySet
from django.utils.timezone import now
from geopy.distance import geodesic

from .fuzzy import calculate_fuzzy_danger
from ..models import Incident

logger = logging.getLogger(__name__)


def estimate_radius(
    origin: Tuple[float, float], destination: Tuple[float, float]
) -> float:
    """
    Estima el radio en metros necesario para cubrir el área entre origen y destino.

    Args:
        origin: Coordenadas del punto de origen.
        destination: Coordenadas del punto de destino.

    Returns:
        Radio en metros para construir el grafo.
    """
    distance_km = geodesic(origin, destination).km
    return min(max(distance_km * 1000 * 1.5, 1000), 3000)


def parse_coordinates(
    post_data: Dict[str, str],
) -> Tuple[float, float, float, float]:
    """
    Extrae y valida coordenadas del cuerpo POST.
    """
    try:
        return (
            float(post_data["origin_lat"]),
            float(post_data["origin_lon"]),
            float(post_data["dest_lat"]),
            float(post_data["dest_lon"]),
        )
    except (KeyError, ValueError) as e:
        raise ValueError("Parámetros inválidos o faltantes") from e


def get_incidents_in_graph(graph: nx.MultiDiGraph) -> QuerySet[Incident]:
    """
    Obtiene todos los incidentes dentro del área cubierta por el grafo.

    Args:
        graph: Grafo de calles.

    Returns:
        Lista de incidentes dentro del área del grafo.
    """
    nodes = list(graph.nodes(data=True))
    lats = [n[1]["y"] for n in nodes]
    lons = [n[1]["x"] for n in nodes]
    bbox = Polygon.from_bbox((min(lons), min(lats), max(lons), max(lats)))
    bbox.srid = 4326  # SRID de Incident.location
    return Incident.objects.filter(location__within=bbox)


def assign_edge_risks(
    graph: nx.MultiDiGraph,
    incidents: QuerySet[Incident],
    risk_radius: int = 50,
    weight_security: float = 0.7,
    speed_mps: float = 50 / 3.6,
) -> None:
    """
    Asigna valores de riesgo y costo combinado a cada arista del grafo.

    Args:
        graph: Grafo de calles.
        incidents: Conjunto de incidentes relevantes.
        risk_radius: Radio de influencia para calcular riesgo.
        weight_security: Peso relativo de la seguridad.
        speed_mps: Velocidad asumida en metros por segundo.
    """
    for u, v, k, data in graph.edges(keys=True, data=True):
        try:
            u_lat, u_lon = graph.nodes[u]["y"], graph.nodes[u]["x"]
            v_lat, v_lon = graph.nodes[v]["y"], graph.nodes[v]["x"]
            midpoint = Point(
                (u_lon + v_lon) / 2, (u_lat + v_lat) / 2, srid=4326
            )

            data["length"] = geodesic((u_lat, u_lon), (v_lat, v_lon)).meters
            nearby = incidents.filter(
                location__distance_lte=(midpoint, D(m=risk_radius))
            )

            if nearby:
                avg_severity = sum(i.severity for i in nearby) / len(nearby)
                avg_time = sum(
                    (now().date() - i.incident_date).days for i in nearby
                ) / len(nearby)
                risk = calculate_fuzzy_danger(
                    len(nearby), avg_severity, risk_radius, avg_time
                )
            else:
                risk = 0.0

            time = data["length"] / speed_mps
            data["risk"] = risk
            data["combined_cost"] = (risk * weight_security) + (
                time * (1 - weight_security)
            )

        except Exception as e:
            logger.warning(f"Error al procesar arista {u}-{v}: {e}")
            data["length"] = 1.0
            data["risk"] = 0.0
            data["combined_cost"] = 1.0
