# core.logic.map_data.py

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from functools import lru_cache
from multiprocessing import Pool

import networkx as nx
import osmnx as ox
import pandas as pd
from django.contrib.gis.geos import Point
from django.utils.timezone import now

from core.logic.config_loader import config
from core.logic.fuzzy_logic import calculate_fuzzy_danger
from core.models import Incidente

ox.settings.log_console = False
ox.settings.use_cache = True


logger = logging.getLogger(__name__)


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


def get_node_coordinates(
    graph: nx.MultiDiGraph, node: int
) -> tuple[float | None, float | None]:
    """
    Obtiene las coordenadas (lat, lon) de un nodo en el grafo.

    Args:
        graph (nx.MultiDiGraph): Grafo de calles.
        node (int): ID del nodo.

    Returns:
        tuple: Coordenadas (lat, lon) del nodo.
    """
    try:
        lat, lon = (float(graph.nodes[node][c]) for c in ("y", "x"))
        return lat, lon
    except KeyError:
        return None, None
    except Exception as e:
        logger.error(
            f"Ocurrió un error al obtener coordenadas del nodo {node}: {e}",
            exc_info=True,
        )
        return None, None


def build_latlon_graph(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Reproyecta el grafo a sistema de coordenadas geográficas (lat/lon).

    Args:
        graph (nx.Graph): Grafo proyectado (en metros).

    Returns:
        nx.Graph: Grafo reproyectado a EPSG:4326 (lat/lon).
    """
    try:
        # Verificar si los nodos tienen coordenadas 'x' y 'y'
        for node, data in list(graph.nodes(data=True)):
            lat, lon = get_node_coordinates(graph, node)
            if lat is None or lon is None:
                logger.warning(f"El nodo {node} no tiene coordenadas definidas.")
                graph.remove_node(node)
            else:
                logger.debug(f"Nodo {node} tiene coordenadas: Lat: {lat}, Lon: {lon}")

        # Si el grafo no tiene un CRS, asignamos uno
        if "crs" not in graph.graph:
            graph.graph["crs"] = "EPSG:3857"  # o el CRS que corresponda

        # Proyectamos el grafo a EPSG:4326 usando to_latlong=True
        project_graph = ox.project_graph(graph, to_latlong=False)

    except Exception as e:
        logger.error(f"Ocurrió un error: {e}", exc_info=True)
        raise
    return project_graph


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
    vigencia = now() - timedelta(days=meses_atras * 30)

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


def get_weighted_risk(coord: tuple[float, float], meses_atras: int = 6) -> float:
    """
    Calcula el riesgo ponderado de una coordenada específica.

    Args:
        coord (tuple): Coordenadas (lat, lon) del punto.
        meses_atras (int): Número de meses hacia atrás para considerar incidentes.

    Returns:
        float: Índice de peligrosidad entre 0 y 1.
    """
    lat, lon = coord
    point = Point(lon, lat, srid=4326)
    vigencia = now() - timedelta(days=meses_atras * 30)

    # Obtener incidentes cercanos
    incidentes = Incidente.objects.filter(
        location__dwithin=(point, config["risk_calculation"]["radius"]),
        fecha_incidente__gte=vigencia,
    )

    num_incidentes = incidentes.count()
    gravedad_promedio = (
        sum(inc.gravedad for inc in incidentes) / num_incidentes
        if num_incidentes > 0
        else 0
    )

    return calculate_fuzzy_danger(num_incidentes, gravedad_promedio)


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


def precalculate_node_risks(graph_latlon: nx.MultiDiGraph) -> dict[int, float]:
    """
    Calcula en paralelo el riesgo difuso de cada nodo del grafo utilizando un ThreadPoolExecutor.

    Args:
        graph_latlon (nx.Graph): Grafo georreferenciado en lat/lon.

    Returns:
        dict[int, float]: Diccionario donde la clave es el ID del nodo y el valor es el riesgo.
    """

    def calc(node: int) -> tuple[int, float]:
        """
        Calcula el riesgo de un nodo.

        Args:
            node (int): ID del nodo.

        Returns:
            tuple[int, float]: Nodo y su riesgo calculado.
        """
        point = get_point_from_node(
            graph_latlon, node
        )  # Obtener las coordenadas del nodo
        risk_value = get_cached_risk(point)  # Obtener el riesgo desde el cache
        return node, risk_value  # Retornar el nodo y su riesgo

    # Usar ThreadPoolExecutor para calcular los riesgos en paralelo
    with ThreadPoolExecutor() as executor:
        # Usamos executor.map para distribuir los cálculos entre los hilos
        results = executor.map(calc, graph_latlon.nodes())

    # Convertimos los resultados a un diccionario
    node_risks = dict(results)

    # Devolver el diccionario con los riesgos calculados
    return node_risks


def compute_risk(
    node: int, node_risks: dict[int, float], graph_latlon: nx.MultiDiGraph
) -> tuple[int, float]:
    """
    Calcula el riesgo de un nodo utilizando los riesgos precalculados.

    Args:
        node (int): ID del nodo.
        node_risks (dict[int, float]): Diccionario con los riesgos precalculados de los nodos.
        graph_latlon (nx.Graph): Grafo en formato geográfico con las coordenadas de los nodos.

    Returns:
        tuple[int, float]: Tupla que contiene el nodo y su riesgo.
    """
    # Verificar si el nodo tiene un riesgo precalculado
    if node in node_risks:
        risk_value = node_risks[node]
    else:
        # Si no está precalculado, calculamos el riesgo utilizando el método cacheado
        point = get_point_from_node(
            graph_latlon, node
        )  # Obtener las coordenadas del nodo
        risk_value = get_cached_risk(point)  # Obtener riesgo desde el cache

    return node, risk_value  # Retornar el nodo y su riesgo


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
        logger.info("Iniciando aplicación de pesos...")
        w_length = 1 - w_safety

        # Filtrar nodos sin coordenadas definidas
        invalid_nodes = tuple(
            node
            for node, data in graph.nodes(data=True)
            if "x" not in data or "y" not in data
        )
        if invalid_nodes:
            for node in invalid_nodes:
                logger.warning(
                    f"El nodo {node} no tiene coordenadas definidas. Se eliminará."
                )
            graph.remove_nodes_from(invalid_nodes)

        # Convertir grafo a DataFrame para procesamiento rápido
        edges_data = tuple(
            (u, v, data.get("length", 1)) for u, v, data in graph.edges(data=True)
        )
        df_edges = pd.DataFrame(edges_data, columns=("u", "v", "length"))
        logger.debug(f"Grafo convertido a DataFrame:\n{df_edges}")

        def compute_risk_for_node(
            node: int, node_risks: dict[int, float], graph: nx.Graph
        ) -> tuple[int, float]:
            """
            Calcular el riesgo para un nodo dado y devolverlo como una tupla (nodo, riesgo).
            """
            return node, compute_risk(node, node_risks, graph)

        # Usar multiprocessing Pool para paralelizar el cálculo del riesgo por nodo
        with Pool() as pool:
            risks = dict(
                pool.map(
                    lambda node: compute_risk_for_node(node, node_risks, graph),
                    graph.nodes(),
                )
            )
        logger.debug(f"Riesgos:\n{risks}")

        # Calcular pesos optimizados
        df_edges["risk"] = df_edges["u"].map(risks) + df_edges["v"].map(risks)
        df_edges["custom_weight"] = (w_safety * df_edges["risk"] / 2) + (
            w_length * df_edges["length"]
        )
        logger.info("Verificando valores de custom_weight antes de continuar:")
        logger.info(df_edges[["u", "v", "custom_weight"]].head())

        # Selección de rutas óptimas usando numpy para mejor rendimiento
        logger.info("Seleccionando las rutas más óptimas...")
        best_edges = df_edges.nsmallest(num_routes, "custom_weight")

        # Construcción de grafo optimizado
        optimal_graph = nx.MultiDiGraph()
        optimal_graph.add_edges_from(
            best_edges[["u", "v", "custom_weight"]].values.tolist(),
            custom_weight=best_edges["custom_weight"].tolist(),
        )

        logger.info(f"Rutas óptimas seleccionadas: {len(optimal_graph.edges)}")
        return optimal_graph

    except Exception as e:
        logger.error(f"Ocurrió un error: {e}", exc_info=True)
        raise


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
