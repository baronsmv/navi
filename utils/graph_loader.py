from pathlib import Path
from typing import Optional

import networkx as nx
import osmnx as ox
from django.contrib.gis.geos import Point, Polygon
from osmnx.truncate import truncate_graph_dist

from .config import cache_locations, PREBUILT_GRAPH_DIR, DYNAMIC_GRAPH_DIR

ox.settings.overpass_endpoint = "https://overpass.kumi.systems/api"


def point_in_graph(graph: nx.MultiDiGraph, point: tuple[float, float]) -> bool:
    """Check if a point is inside the graph's bounding box."""
    nodes = ox.graph_to_gdfs(graph, edges=False)
    bounds = nodes.total_bounds  # [minx, miny, maxx, maxy]
    bbox = Polygon.from_bbox((bounds[0], bounds[1], bounds[2], bounds[3]))
    point_geom = Point(point[1], point[0])  # lon, lat
    return bbox.contains(point_geom)


def graph_contains(
    graph: nx.MultiDiGraph,
    origin: tuple[float, float],
    destination: tuple[float, float],
) -> bool:
    return point_in_graph(graph, origin) and point_in_graph(graph, destination)


def find_graph_for_route(
    origin: tuple[float, float], destination: tuple[float, float]
) -> Optional[Path]:
    for name in cache_locations.keys():
        path = PREBUILT_GRAPH_DIR / f"{name}.graphml"
        if path.exists():
            graph = ox.load_graphml(path)
            if graph_contains(graph, origin, destination):
                return path

    for path in DYNAMIC_GRAPH_DIR.glob("*.graphml"):
        graph = ox.load_graphml(path)
        if graph_contains(graph, origin, destination):
            return path

    return None


def get_local_subgraph(graph, origin, destination, buffer_m=2000):
    mid_lat = (origin[0] + destination[0]) / 2
    mid_lon = (origin[1] + destination[1]) / 2
    source_node = ox.distance.nearest_nodes(graph, mid_lon, mid_lat)

    return truncate_graph_dist(
        graph, source_node, dist=buffer_m, weight="length"
    )


def save_dynamic_graph(center: tuple[float, float], radius_m: float) -> Path:
    graph = ox.graph_from_point(center, dist=radius_m, network_type="drive")
    filename = (
        f"{round(center[0], 4)}_{round(center[1], 4)}_{radius_m}.graphml"
    )
    path = DYNAMIC_GRAPH_DIR / filename
    ox.save_graphml(graph, path)
    return path
