import logging

import networkx as nx
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.utils.timezone import now
from geopy.distance import geodesic
from numpy import average

from core.logic.fuzzy_logic import calculate_fuzzy_danger
from core.models import Incident
from utils.config_loader import config

logger = logging.getLogger(__name__)


def node_incidents(node_lat, node_lon, radius=config["risk_calculation"]["radius"]):
    """
    Obtiene los incidentes cercanos a un nodo en el grafo dentro de un radio especificado.

    Args:
        node_lat (float): Latitud del nodo.
        node_lon (float): Longitud del nodo.
        radius (int): Radio en metros dentro del cual buscar los incidentes.

    Returns:
        tuple: Lista de incidentes cercanos.
    """
    node_point = Point(node_lon, node_lat, srid=4326)
    incidents = Incident.objects.filter(
        location__distance_lte=(node_point, D(m=radius))
    )
    return tuple(incidents)


def route_incidents(graph, route, radius=config["risk_calculation"]["radius"]):
    """
    Recolecta todos los incidentes de los nodos en la ruta.

    Args:
        graph (networkx.Graph): Grafo con los nodos y sus coordenadas.
        route (list): Ruta de nodos.
        radius (int): Radio para buscar los incidentes cercanos.

    Returns:
        set: Un conjunto con los incidentes, el nodo más cercano de la ruta y la distancia.
    """
    return {
        incident
        for node in route
        for incident in node_incidents(
            graph.nodes[node]["y"], graph.nodes[node]["x"], radius
        )
    }


def incidents_distance(incidents, route, graph):
    """
    Para cada incidente, encuentra el nodo más cercano de la ruta y la distancia a él.

    Args:
        incidents (set): Lista de incidentes.
        route (list): Ruta de nodos.
        graph (networkx.Graph): Grafo con los nodos y sus coordenadas.

    Returns:
        tuple: Una tupla con los incidentes, el nodo más cercano de la ruta y la distancia.
    """
    incident_info = []

    for incidente in incidents:
        # Coordenadas del incidente
        incident_lat = incidente.location.y
        incident_lon = incidente.location.x

        # Buscar el nodo más cercano en la ruta
        nearest_node = None
        min_distance = float("inf")

        for node in route:
            node_lat = graph.nodes[node]["y"]
            node_lon = graph.nodes[node]["x"]

            # Calcular la distancia entre el incidente y el nodo de la ruta
            distance = geodesic(
                (incident_lat, incident_lon), (node_lat, node_lon)
            ).meters

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        # Añadir el incidente con su nodo más cercano de la ruta y distancia
        incident_info.append((incidente, nearest_node, min_distance))

    # Retornar como tupla
    return tuple(incident_info)


def weighted_average(values: tuple):
    return float(average(values, weights=tuple(1 / d if d != 0 else 1 for d in values)))


def route_risk(incidents, graph, route):
    """
    Calcula el riesgo total de todos los nodos de la ruta.

    Args:
        incidents (set): Lista de incidentes.
        graph (networkx.Graph): Grafo con los nodos y sus coordenadas.
        route (list): Ruta de nodos.

    Returns:
        float: Riesgo de la ruta.
    """
    if not incidents:
        return 0.0  # No hay incidentes, ruta segura

    distances = tuple(i[2] for i in incidents_distance(incidents, route, graph))

    current_date = now().date()
    times = tuple((current_date - i.incident_date).days for i in incidents)

    num_incidents = len(incidents)
    avg_gravity = sum([incidente.severity for incidente in incidents]) / num_incidents
    risk_zone_distance = weighted_average(distances)
    time = weighted_average(times)

    return calculate_fuzzy_danger(num_incidents, avg_gravity, risk_zone_distance, time)


def calculate_combined_cost(
    graph,
    weight_security: int = config["risk_calculation"]["w_safety"],
):
    """
    Asigna un costo combinado (seguridad y rapidez) a cada arista del grafo,
    evaluando internamente el riesgo de la ruta en función de los incidentes cercanos.

    Args:
        graph (networkx.Graph): Grafo con información de nodos y aristas.
        weight_security (int): Valor de importancia de la seguridad.

    Returns:
        networkx.Graph: Grafo con los costos combinados asignados.
    """
    # Calcular el peso de la rapidez basado en el peso de seguridad
    weight_speed = 1 - weight_security

    # Recorrer todas las aristas del grafo
    for u, v, data in graph.edges(data=True):
        # Encontramos la ruta más corta entre u y v
        route_nodes = nx.shortest_path(graph, u, v, weight="combined_cost")

        # Obtener los incidentes que afectan la ruta utilizando route_incidents
        incidents = route_incidents(graph, route_nodes)

        # Calculamos el riesgo total de la ruta utilizando route_risk
        route_risk_value = route_risk(incidents, graph, route_nodes)

        # Obtenemos la distancia de la arista
        distance = data["length"]

        # Calcular tiempo de viaje (suponemos una velocidad constante)
        speed = 50 / 3.6  # Velocidad en metros por segundo
        travel_time = distance / speed  # Tiempo de viaje en segundos

        # Calcular el costo combinado: seguridad (según el riesgo de la ruta) + tiempo
        combined_cost = (route_risk_value * weight_security) + (
            travel_time * weight_speed
        )

        # Asignamos el costo combinado a la arista
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
