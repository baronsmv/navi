import logging
from typing import Dict, List, Tuple

import networkx as nx
import osmnx as ox
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils.timezone import now
from geopy.distance import geodesic

from core.logic.fuzzy_logic import calculate_fuzzy_danger
from core.models import Incident

logger = logging.getLogger(__name__)


def parse_coordinates(
    post_data: Dict[str, str],
) -> Tuple[float, float, float, float]:
    try:
        return (
            float(post_data["origin_lat"]),
            float(post_data["origin_lon"]),
            float(post_data["dest_lat"]),
            float(post_data["dest_lon"]),
        )
    except (KeyError, ValueError) as e:
        raise ValueError("Parámetros inválidos o faltantes") from e


def build_graph_with_risk(
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    radius_m: int = 10000,
    risk_radius: int = 50,
    weight_security: float = 0.7,
) -> nx.MultiDiGraph:
    center = (
        (origin[0] + destination[0]) / 2,
        (origin[1] + destination[1]) / 2,
    )
    graph = ox.graph_from_point(center, dist=radius_m, network_type="drive")

    for u, v, k, data in graph.edges(keys=True, data=True):
        try:
            u_lat, u_lon = graph.nodes[u]["y"], graph.nodes[u]["x"]
            v_lat, v_lon = graph.nodes[v]["y"], graph.nodes[v]["x"]
            midpoint = ((u_lat + v_lat) / 2, (u_lon + v_lon) / 2)

            # Distance
            length = geodesic((u_lat, u_lon), (v_lat, v_lon)).meters
            data["length"] = length

            # Risk
            point = Point(midpoint[1], midpoint[0], srid=4326)
            incidents = Incident.objects.filter(
                location__distance_lte=(point, D(m=risk_radius))
            )
            if incidents:
                avg_severity = sum(i.severity for i in incidents) / len(
                    incidents
                )
                days_since = [
                    (now().date() - i.incident_date).days for i in incidents
                ]
                avg_time = sum(days_since) / len(days_since)
                data["risk"] = calculate_fuzzy_danger(
                    len(incidents), avg_severity, risk_radius, avg_time
                )
            else:
                data["risk"] = 0.0

            # Combined cost
            speed = 50 / 3.6  # m/s
            time = length / speed
            weight_speed = 1 - weight_security
            data["combined_cost"] = (data["risk"] * weight_security) + (
                time * weight_speed
            )

        except Exception as e:
            logger.warning(f"Error procesando arista {u}-{v}: {e}")
            data["length"] = 1.0
            data["risk"] = 0.0
            data["combined_cost"] = 1.0

    return graph


def get_route(
    graph: nx.MultiDiGraph,
    origin: Tuple[float, float],
    destination: Tuple[float, float],
) -> Tuple[List[int], int, int]:
    origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
    dest_node = ox.distance.nearest_nodes(
        graph, destination[1], destination[0]
    )

    try:
        route = nx.dijkstra_path(
            graph, origin_node, dest_node, weight="combined_cost"
        )
    except nx.NetworkXNoPath:
        logger.warning("No se encontró ruta entre los nodos.")
        return [], origin_node, dest_node

    return route, origin_node, dest_node


def extract_route_coords(
    graph: nx.MultiDiGraph, route: List[int]
) -> List[Tuple[float, float]]:
    return [
        (
            graph.nodes[node]["y"],
            graph.nodes[node]["x"],
        )  # [lat, lon] for Leaflet
        for node in route
        if "x" in graph.nodes[node] and "y" in graph.nodes[node]
    ]


def get_route_risk(graph: nx.MultiDiGraph, route: List[int]) -> float:
    risks = []
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        for k in graph[u][v]:
            risks.append(graph[u][v][k].get("risk", 0.0))
    return max(risks) if risks else 0.0
