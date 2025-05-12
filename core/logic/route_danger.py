import logging

import networkx as nx
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from core.logic.fuzzy_logic import calculate_fuzzy_danger
from core.models import Incident
from utils.config_loader import config

logger = logging.getLogger(__name__)


def get_nearby_incidents(
    node_lat, node_lon, radius=config["risk_calculation"]["radius"]
):
    """
    Obtiene los incidentes cercanos a un nodo en el grafo dentro de un radio especificado.

    Args:
        node_lat (float): Latitud del nodo.
        node_lon (float): Longitud del nodo.
        radius (int): Radio en metros dentro del cual buscar los incidentes.

    Returns:
        list: Lista de incidentes cercanos.
    """
    node_point = Point(node_lon, node_lat, srid=4326)
    incidents = Incident.objects.filter(
        location__distance_lte=(node_point, D(m=radius))
    )
    return list(incidents)


def calculate_route_risk(
    node_lat, node_lon, radius=config["risk_calculation"]["radius"]
):
    """
    Calcula el nivel de peligro de una ruta (arista) basada en los incidentes cercanos.

    Args:
        node_lat (float): Latitud del nodo.
        node_lon (float): Longitud del nodo.
        radius (int): Radio en metros dentro del cual buscar los incidentes.

    Returns:
        float: Índice de peligrosidad de la ruta.
    """
    incidents = get_nearby_incidents(node_lat, node_lon, radius)

    if not incidents:
        return 0.0  # No hay incidentes, ruta segura

    # Calcular el número de incidentes y la gravedad promedio
    num_incidents = len(incidents)
    avg_gravity = sum([incidente.severity for incidente in incidents]) / num_incidents

    # Calcular el riesgo usando la lógica difusa
    risk = calculate_fuzzy_danger(num_incidents, avg_gravity)
    return risk


def calculate_combined_cost(
    graph,
    radius: int = config["risk_calculation"]["radius"],
    weight_security: int = config["risk_calculation"]["w_safety"],
):
    """
    Asigna un costo combinado (seguridad y rapidez) a cada arista del grafo.

    Args:
        graph (networkx.Graph): Grafo con información de nodos y aristas.
        radius (int): Radio para considerar los incidentes cercanos.
        weight_security (int): Valor de importancia de la seguridad.

    Returns:
        networkx.Graph: Grafo con los costos combinados asignados.
    """
    weight_speed = 1 - weight_security
    for u, v, data in graph.edges(data=True):
        route_nodes = nx.shortest_path(graph, u, v, weight="combined_cost")
        total_risk = 0
        for node in route_nodes:
            node_lat, node_lon = graph.nodes[node]["y"], graph.nodes[node]["x"]
            total_risk += calculate_route_risk(node_lat, node_lon, radius)

        avg_risk = total_risk / len(route_nodes)
        distance = data["length"]

        speed = 50 / 3.6  # Velocidad en metros por segundo
        travel_time = distance / speed  # Tiempo de viaje en segundos

        combined_cost = (avg_risk * weight_security) + (travel_time * weight_speed)
        data["combined_cost"] = combined_cost

    return graph


def find_optimal_route(graph, origin_node, dest_node):
    """
    Encuentra la ruta más corta basada en el costo combinado de seguridad y rapidez.

    Args:
        graph (networkx.Graph): Grafo con los costos combinados.
        origin_node (int): Nodo de origen.
        dest_node (int): Nodo de destino.

    Returns:
        list: Ruta más corta (lista de nodos).
    """
    # Calcular la ruta más corta según el costo combinado
    route = nx.shortest_path(graph, origin_node, dest_node, weight="combined_cost")
    return route
