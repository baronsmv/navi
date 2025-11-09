import logging
from typing import List

import networkx as nx

logger = logging.getLogger(__name__)


def get_route_risk(graph: nx.MultiDiGraph, route: List[int]) -> float:
    """
    Calcula el nivel de riesgo de una ruta basado en los valores de riesgo
    preasignados a las aristas del grafo.

    Args:
        graph: Grafo con valores de 'risk' en las aristas.
        route: Lista de nodos que forman la ruta.

    Returns:
        Valor de riesgo máximo de la ruta (0.0 a 1.0).
    """
    risks = []
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        for k in graph[u][v]:
            risks.append(graph[u][v][k].get("risk", 0.0))

    return max(risks) if risks else 0.0


def get_route_length(graph: nx.MultiDiGraph, route: List[int]) -> float:
    """
    Suma la longitud total de una ruta.

    Args:
        graph: Grafo con atributo 'length' en las aristas.
        route: Lista de nodos que forman la ruta.

    Returns:
        Longitud total en metros.
    """
    total = 0.0
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        min_length = min(
            (data.get("length", 1.0) for data in graph[u][v].values()),
            default=1.0,
        )
        total += min_length
    return total
