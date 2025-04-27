# core.logic.route_planner.py

import networkx as nx

from core.logic.fuzzy_logic import calculate_fuzzy_danger
from core.logic.map_data import (
    apply_custom_weights,
    build_latlon_graph,
    get_point_from_node,
    get_safest_route,
    get_incidents_near_route,
)


def calculate_route_risk(route_coords: list[tuple[float, float]]) -> float:
    """
    Calcula la peligrosidad global de una ruta a partir de sus coordenadas.

    Args:
        route_coords (list): Lista de coordenadas (lat, lon) de la ruta.

    Returns:
        float: Nivel difuso de peligrosidad (0-1).
    """
    incidents = get_incidents_near_route(route_coords)
    avg_gravity = (
        sum(inc.gravedad for inc in incidents) / max(len(incidents), 1)
        if incidents
        else 0
    )
    return calculate_fuzzy_danger(len(incidents), avg_gravity)


def get_optimized_routes(
    graph: nx.MultiDiGraph,
    origin_node: int,
    dest_node: int,
    safety_weights: list[float] = [0.6, 0.8, 1.0],
) -> list[dict]:
    """
    Obtiene rutas optimizadas para distintas prioridades de seguridad.

    Args:
        graph (nx.MultiDiGraph): Grafo proyectado (en metros).
        origin_node (int): Nodo de inicio.
        dest_node (int): Nodo de destino.
        safety_weights (list): Lista de pesos para el riesgo (0 a 1).

    Returns:
        list[dict]: Lista con datos de cada ruta (coordenadas, peligrosidad, peso usado).
    """
    graph_latlon = build_latlon_graph(graph)
    rutas = []

    for w_safety in safety_weights:
        graph_safe = apply_custom_weights(graph, w_safety)
        ruta = get_safest_route(graph_safe, origin_node, dest_node)

        if not ruta:
            rutas.append(
                {
                    "ruta": [],
                    "coordenadas": [],
                    "peligrosidad": None,
                    "seguridad": w_safety,
                }
            )
            continue

        coords = [
            get_point_from_node(graph_latlon, node).coords[0][::-1] for node in ruta
        ]
        danger = calculate_route_risk(coords)

        rutas.append(
            {
                "ruta": ruta,
                "coordenadas": coords,
                "peligrosidad": danger,
                "seguridad": w_safety,
            }
        )

    return rutas
