import itertools
import logging
from typing import List, Set, Tuple

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


def node_incidents(
    node_lat: float, node_lon: float, radius: int = config["risk_calculation"]["radius"]
) -> Tuple[Incident, ...]:
    """
    Busca incidentes cercanos a un nodo geográfico dentro de un radio dado.

    Args:
        node_lat (float): Latitud del nodo.
        node_lon (float): Longitud del nodo.
        radius (int): Radio en metros para buscar incidentes.

    Returns:
        Tupla de incidentes encontrados.
    """
    node_point = Point(node_lon, node_lat, srid=4326)  # Crear punto geográfico
    incidents = Incident.objects.filter(
        location__distance_lte=(node_point, D(m=radius))  # Buscar incidentes cercanos
    )
    return tuple(incidents)


def route_incidents(
    graph: nx.Graph, route: List, radius: int = config["risk_calculation"]["radius"]
) -> Set[Incident]:
    """
    Recolecta todos los incidentes de los nodos en la ruta.

    Args:
        graph: Grafo con los nodos y sus coordenadas.
        route: Ruta de nodos.
        radius: Radio para buscar los incidentes cercanos.

    Returns:
        Conjunto de incidentes únicos cercanos a la ruta.
    """
    return {
        incident
        for node in route
        for incident in node_incidents(
            graph.nodes[node]["y"], graph.nodes[node]["x"], radius
        )
    }


def incidents_distance(
    incidents: Set[Incident], route: list, graph: nx.Graph
) -> Tuple[Tuple[Incident, int, float], ...]:
    """
    Para cada incidente, encuentra el nodo más cercano de la ruta y la distancia a él.

    Args:
        incidents: Lista de incidentes.
        route: Ruta de nodos.
        graph: Grafo con los nodos y sus coordenadas.

    Returns:
        Tupla de (incidente, nodo más cercano, distancia en metros).
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


def weighted_average(values: Tuple[float, ...]) -> float:
    """
    Calcula el promedio ponderado, donde los valores más cercanos tienen más peso.

    Returns:
        Promedio ponderado.
    """
    return float(average(values, weights=tuple(1 / d if d != 0 else 1 for d in values)))


def route_risk(incidents: Set[Incident], graph: nx.Graph, route: list) -> float:
    """
    Calcula el riesgo total de una ruta basado en incidentes cercanos.

    Args:
        incidents: Lista de incidentes.
        graph: Grafo con los nodos y sus coordenadas.
        route: Ruta de nodos.

    Returns:
        Valor de riesgo calculado.
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


def calculate_route_cost(
    graph: nx.Graph, route_nodes: list, weight_security: float, weight_speed: float
) -> float:
    """
    Calcula el costo combinado de una ruta dada, considerando seguridad y rapidez.

    Args:
        graph: Grafo con los nodos y sus aristas.
        route_nodes: Lista de nodos que forman la ruta.
        weight_security: Peso para la seguridad (riesgo).
        weight_speed: Peso para la rapidez (tiempo de viaje).

    Returns:
        Costo combinado de la ruta.
    """
    # Obtener los incidentes que afectan la ruta utilizando route_incidents
    incidents = route_incidents(graph, route_nodes)
    logger.info(f"Incidentes en la ruta {route_nodes}: {incidents}")

    # Calcular el riesgo total de la ruta utilizando route_risk
    route_risk_value = route_risk(incidents, graph, route_nodes)
    logger.info(f"Valor del riesgo de la ruta {route_nodes}: {route_risk_value}")

    # Calcular la distancia total de la ruta
    total_distance = 0
    for i in range(len(route_nodes) - 1):
        u, v = route_nodes[i], route_nodes[i + 1]
        edge_data = graph[u][v]  # Datos de la arista entre u y v

        # Verificar si la arista tiene el atributo 'length'
        if "length" not in edge_data:
            logger.warning(f"Arista entre {u} y {v} NO tiene atributo 'length'.")
            continue  # Omite la arista si no tiene 'length'

        total_distance += edge_data["length"]  # Sumar la longitud de la arista

    logger.info(f"Distancia total de la ruta {route_nodes}: {total_distance} metros")

    # Calcular el tiempo de viaje para la ruta (suponiendo una velocidad constante)
    speed = 50 / 3.6  # Velocidad en metros por segundo
    travel_time = total_distance / speed  # Tiempo de viaje en segundos
    logger.info(
        f"Tiempo de viaje estimado para la ruta {route_nodes}: {travel_time} segundos"
    )

    # Calcular el costo combinado para esta ruta
    combined_cost = (route_risk_value * weight_security) + (travel_time * weight_speed)
    logger.info(
        f"Costo combinado para la ruta {route_nodes}: {combined_cost} (seguridad: {route_risk_value * weight_security}, rapidez: {travel_time * weight_speed})"
    )

    return combined_cost


def calculate_best_route_cost(
    graph: nx.Graph, u: int, v: int, weight_security: float, weight_speed: float
) -> Tuple[List, float]:
    """
    Encuentra la mejor ruta entre dos nodos según el costo combinado.

    Args:
        graph: Grafo con los nodos y sus aristas.
        u: Nodo de origen.
        v: Nodo de destino.
        weight_security: Peso para la seguridad (riesgo).
        weight_speed: Peso para la rapidez (tiempo de viaje).

    Returns:
        Ruta óptima y su costo.
    """
    # Calcular el grafo con costos combinados
    graph_with_combined_cost = graph.copy()

    # Asignar el costo combinado a cada arista del grafo
    for u, v, data in graph_with_combined_cost.edges(data=True):
        # Aquí usamos el costo combinado ya calculado para la arista
        data["combined_cost"] = calculate_route_cost(
            graph, [u, v], weight_security, weight_speed
        )

    # Encontrar la mejor ruta entre u y v usando Dijkstra basado en el "combined_cost"
    best_route = nx.dijkstra_path(
        graph_with_combined_cost, source=u, target=v, weight="combined_cost"
    )
    best_combined_cost = nx.dijkstra_path_length(
        graph_with_combined_cost, source=u, target=v, weight="combined_cost"
    )

    return best_route, best_combined_cost


def calculate_combined_cost(
    graph: nx.Graph, weight_security: int = config["risk_calculation"]["w_safety"]
) -> Tuple[nx.Graph, dict]:
    """
    Asigna costos combinados a todas las rutas posibles en el grafo.

    Args:
        graph: Grafo con información de nodos y aristas.
        weight_security: Valor de importancia de la seguridad.

    Returns:
        Grafo actualizado y rutas óptimas.
    """
    # Asegurarse de trabajar con una copia mutable del grafo
    graph = graph.copy()

    # Calcular el peso de la rapidez basado en el peso de seguridad
    weight_speed = 1 - weight_security

    # Diccionario para almacenar las mejores rutas entre nodos
    best_routes = {}

    # Recorrer todos los pares de nodos del grafo de forma más eficiente
    for u, v in itertools.combinations(graph.nodes, 2):  # solo par de nodos
        # Obtener la mejor ruta y su costo combinado entre u y v
        best_route, best_combined_cost = calculate_best_route_cost(
            graph, u, v, weight_security, weight_speed
        )

        if best_route:
            # Asegurarnos de que el grafo sea mutable (esto garantiza que podemos asignar valores)
            for i in range(len(best_route) - 1):
                # Asignamos el costo combinado a cada arista de la mejor ruta
                graph.edges[best_route[i], best_route[i + 1]][
                    "combined_cost"
                ] = best_combined_cost

            # Almacenamos la mejor ruta y su costo combinado
            best_routes[(u, v)] = {
                "route": best_route,
                "combined_cost": best_combined_cost,
            }

    return graph, best_routes
