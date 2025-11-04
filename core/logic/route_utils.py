import logging

import osmnx as ox
from geopy.distance import geodesic

from core.logic.route_danger import calculate_best_route_cost

logger = logging.getLogger(__name__)


def parse_coordinates(post_data):
    try:
        origin_lat = float(post_data["origin_lat"])
        origin_lon = float(post_data["origin_lon"])
        dest_lat = float(post_data["dest_lat"])
        dest_lon = float(post_data["dest_lon"])
        return origin_lat, origin_lon, dest_lat, dest_lon
    except (KeyError, ValueError) as e:
        raise ValueError("Parámetros inválidos o faltantes") from e


def get_graph(origin, destination):
    """
    Obtiene un grafo de OpenStreetMap alrededor de un área centrada en el punto medio
    entre las coordenadas de origen y destino, y añade el atributo 'length' a las aristas
    para calcular distancias entre nodos.

    Args:
        origin (tuple): Coordenadas del punto de origen (latitud, longitud).
        destination (tuple): Coordenadas del punto de destino (latitud, longitud).

    Returns:
        networkx.Graph: Grafo generado de OpenStreetMap con el atributo 'length' agregado a las aristas.

    Notes:
        - La función calcula el centro geográfico entre el origen y el destino y obtiene el grafo
          de OpenStreetMap en un radio de hasta 70 km, dependiendo de la distancia entre ambos puntos.
        - Después de obtener el grafo, se añade el atributo 'length' a las aristas para permitir
          el cálculo de distancias y costos de las rutas.
    """
    # Calcular la distancia en kilómetros entre origen y destino
    distance_km = geodesic(origin, destination).km
    # Limitar el radio a 70 km como máximo
    radius_m = min(distance_km, 70) * 1000  # Convertir a metros
    # Calcular las coordenadas medias (centro geográfico) entre origen y destino
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2

    # Obtener el grafo de OpenStreetMap en un radio determinado desde el centro
    graph = ox.graph_from_point((mid_lat, mid_lon), dist=radius_m, network_type="all")

    # Calcular y agregar el atributo 'length' a las aristas
    for u, v, data in graph.edges(data=True):
        # Verificar si los nodos tienen las coordenadas 'x' y 'y'
        if u not in graph.nodes or v not in graph.nodes:
            continue  # Si un nodo no tiene coordenadas, omitir esta arista

        # Obtener las coordenadas de los nodos u y v
        u_lat, u_lon = graph.nodes[u]["y"], graph.nodes[u]["x"]
        v_lat, v_lon = graph.nodes[v]["y"], graph.nodes[v]["x"]

        # Calcular la distancia entre los nodos u y v (en metros)
        length = geodesic((u_lat, u_lon), (v_lat, v_lon)).meters

        # Asignar el valor de la longitud de la arista
        data["length"] = length

    # Verificar que todas las aristas tienen la longitud
    for u, v, data in graph.edges(data=True):
        if "length" not in data:
            print(f"Arista de {u} a {v} NO tiene atributo 'length'")

    return graph


def get_route(graph, graph_with_cost, origin, destination, weight_security=0.5):
    # Obtener los nodos más cercanos a las coordenadas de origen y destino
    origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
    dest_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])

    # Calcular la mejor ruta entre los nodos de origen y destino, usando el grafo con costos
    best_route, _ = calculate_best_route_cost(
        graph_with_cost,
        origin_node,
        dest_node,
        weight_security,
        weight_speed=1 - weight_security,
    )

    return best_route, origin_node, dest_node


def extract_route_coords(graph, route):
    return [(graph.nodes[node]["y"], graph.nodes[node]["x"]) for node in route]
