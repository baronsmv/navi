import logging

import osmnx as ox
from geopy.distance import geodesic

from core.logic.route_danger import (
    find_optimal_route,
)

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
    distance_km = geodesic(origin, destination).km
    radius_m = min(distance_km, 70) * 1000
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2
    graph = ox.graph_from_point((mid_lat, mid_lon), dist=radius_m, network_type="all")
    return graph


def get_route(graph, graph_with_cost, origin, destination):
    origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
    dest_node = ox.distance.nearest_nodes(graph, destination[1], destination[0])
    route = find_optimal_route(graph_with_cost, origin_node, dest_node)
    return route, origin_node, dest_node


def extract_route_coords(graph, route):
    return [(graph.nodes[node]["y"], graph.nodes[node]["x"]) for node in route]
