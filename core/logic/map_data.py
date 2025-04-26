import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache
from multiprocessing import Pool

import networkx as nx
import osmnx as ox
import pandas as pd
from django.contrib.gis.geos import Point

from core.logic.config_loader import config
from core.logic.fuzzy_logic import get_weighted_risk
from core.models import Incidente

ox.settings.log_console = False
ox.settings.use_cache = True


def get_graph(
    place_name: str, mode: str = "walk", project: bool = True
) -> nx.MultiDiGraph:
    """
    Obtiene el grafo de calles de un lugar utilizando OSMnx.

    Args:
        place_name (str): Nombre del lugar a buscar.
        mode (str): Tipo de red ('walk', 'drive', 'bike').
        project (bool): Si se debe proyectar el grafo a coordenadas métricas.

    Returns:
        nx.MultiDiGraph: Grafo de calles del lugar.
    """
    graph = ox.graph_from_place(place_name, network_type=mode)
    return ox.project_graph(graph) if project else graph


def build_latlon_graph(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Reproyecta el grafo a sistema de coordenadas geográficas (lat/lon).

    Args:
        graph (nx.Graph): Grafo proyectado (en metros).

    Returns:
        nx.Graph: Grafo reproyectado a EPSG:4326 (lat/lon).
    """
    return ox.project_graph(graph, to_crs="EPSG:4326")


def get_node_coordinates(graph: nx.MultiDiGraph, node: int) -> tuple[float, float]:
    """
    Obtiene las coordenadas (lat, lon) de un nodo en el grafo.

    Args:
        graph (nx.MultiDiGraph): Grafo de calles.
        node (int): ID del nodo.

    Returns:
        tuple: Coordenadas (lat, lon) del nodo.
    """
    lat = float(graph.nodes[node]["y"])
    lon = float(graph.nodes[node]["x"])
    return lat, lon


def get_nearest_node(graph: nx.MultiDiGraph, point: tuple[float, float]) -> int:
    """
    Obtiene el nodo más cercano a unas coordenadas geográficas.

    Args:
        graph (nx.MultiDiGraph): Grafo de calles.
        point (tuple): Coordenadas (lat, lon) del punto de interés.

    Returns:
        int: ID del nodo más cercano.
    """
    lat, lon = point
    return ox.distance.nearest_nodes(graph, X=lon, Y=lat)


def get_point_from_node(graph_latlon: nx.MultiDiGraph, node: int) -> Point:
    """
    Devuelve las coordenadas geográficas de un nodo como objeto Point.

    Args:
        graph_latlon (nx.MultiDiGraph): Grafo en EPSG:4326.
        node (int): ID del nodo.

    Returns:
        Point: Punto geo-espacial del nodo.
    """
    lon = float(graph_latlon.nodes[node]["x"])
    lat = float(graph_latlon.nodes[node]["y"])
    return Point((lon, lat), srid=4326)


def get_incidents_near_route(
    route_coords: list[tuple[float, float]], meses_atras: int = 6
) -> list[Incidente]:
    """
    Filtra incidentes recientes cercanos a una ruta definida por una lista de coordenadas.

    Args:
        route_coords (list): Lista de coordenadas (lat, lon) que definen la ruta.
        meses_atras (int, opcional): Número de meses hacia atrás para filtrar incidentes. Por defecto 6.

    Returns:
        list[Incidente]: Lista de incidentes cercanos a la ruta.
    """
    vigencia = datetime.now() - timedelta(days=meses_atras * 30)

    # Lista para almacenar todos los incidentes encontrados en la zona de la ruta
    incidentes_cercanos = []

    # Para cada coordenada de la ruta, obtenemos los incidentes cercanos
    for coord in route_coords:
        point = Point(
            coord[1], coord[0], srid=4326
        )  # Crear el objeto Point para la coordenada (lon, lat)

        # Filtrar incidentes cercanos al punto, dentro de un radio definido
        incidents = Incidente.objects.filter(
            location__dwithin=(
                point,
                config["risk_calculation"]["radius"],
            ),  # Usar el radio desde la configuración
            fecha_incidente__gte=vigencia,  # Filtrar por fecha de los últimos meses
        ).order_by("fecha_incidente")

        # Agregar los incidentes a la lista total
        incidentes_cercanos.extend(incidents)

    return incidentes_cercanos


@lru_cache(maxsize=None)
def get_cached_risk(point: Point) -> float:
    """
    Calcula y cachea el riesgo de un nodo, considerando el tiempo de los incidentes.

    Args:
        point (Point): Ubicación geográfica del nodo.

    Returns:
        float: Índice de peligrosidad entre 0 y 1, ajustado por tiempo.
    """
    return get_weighted_risk((point.y, point.x))


def precalculate_node_risks(graph_latlon: nx.Graph) -> dict[int, float]:
    """
    Calcula en paralelo el riesgo difuso de cada nodo del grafo.

    Args:
        graph_latlon (nx.Graph): Grafo georreferenciado en lat/lon.

    Returns:
        dict[int, float]: Mapeo nodo -> nivel de riesgo.
    """

    def calc(node: int) -> tuple[int, float]:
        point = get_point_from_node(graph_latlon, node)
        return node, get_cached_risk(point)

    with ThreadPoolExecutor() as executor:
        results = executor.map(calc, graph_latlon.nodes())
    return dict(results)


def compute_risk(node_data):
    """Función auxiliar para calcular el riesgo de un nodo."""
    u, node_risks = node_data
    return u, node_risks[u]


def apply_custom_weights(
    graph: nx.MultiDiGraph,
    w_safety: float = config["risk_calculation"]["w_safety"],
    num_routes: int = 30,
) -> nx.MultiDiGraph:
    """
    Aplica pesos personalizados y selecciona las rutas más óptimas con mejoras de rendimiento.

    Args:
        graph (nx.MultiDiGraph): Grafo original de calles (DiGraph para menos sobrecarga).
        w_safety (float): Peso relativo del riesgo (0-1).
        num_routes (int): Número máximo de rutas óptimas.

    Returns:
        nx.DiGraph: Grafo con pesos personalizados y rutas óptimas.
    """
    try:
        print("Iniciando aplicación de pesos...", flush=True)
        w_length = 1 - w_safety

        # Convertir grafo a DataFrame para procesamiento rápido
        edges_data = []
        for u, v, data in graph.edges(data=True):
            length = data.get("length", 1)
            edges_data.append((u, v, length))

        df_edges = pd.DataFrame(edges_data, columns=["u", "v", "length"])

        # Precalcular riesgos por nodo en paralelo
        print("Precalculando riesgos por nodo en paralelo...", flush=True)
        node_risks = precalculate_node_risks(graph)

        with Pool() as pool:
            risks = dict(
                pool.map(compute_risk, [(u, node_risks) for u in graph.nodes()])
            )

        # Calcular pesos optimizados
        df_edges["risk"] = df_edges["u"].map(risks) + df_edges["v"].map(risks)
        df_edges["custom_weight"] = (w_safety * df_edges["risk"] / 2) + (
            w_length * df_edges["length"]
        )

        # Selección de rutas óptimas usando numpy para mejor rendimiento
        print("Seleccionando las rutas más óptimas...", flush=True)
        best_edges = df_edges.nsmallest(num_routes, "custom_weight")

        # Construcción de grafo optimizado
        optimal_graph = nx.MultiDiGraph()
        optimal_graph.add_edges_from(
            best_edges[["u", "v", "custom_weight"]].values.tolist(),
            custom_weight=best_edges["custom_weight"].tolist(),
        )

        print(f"Rutas óptimas seleccionadas: {len(optimal_graph.edges)}", flush=True)
        return optimal_graph

    except Exception as e:
        print(f"Error en apply_custom_weights:\n\n{traceback.format_exc()}", flush=True)
        raise e


def get_safest_route(
    graph: nx.MultiDiGraph, origin_node: int, dest_node: int
) -> list[int]:
    """
    Calcula la ruta más segura entre dos nodos usando pesos personalizados.

    Args:
        graph (nx.MultiDiGraph): Grafo de calles.
        origin_node (int): Nodo de inicio.
        dest_node (int): Nodo de destino.

    Returns:
        list[int]: Lista de nodos que forman la ruta más segura.
    """
    graph_safe = apply_custom_weights(graph)

    try:
        return nx.shortest_path(
            graph_safe,
            source=origin_node,
            target=dest_node,
            weight="custom_weight",
            method="dijkstra",
        )
    except nx.NetworkXNoPath:
        return []  # No hay ruta disponible
