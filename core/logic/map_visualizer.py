import folium

from core.logic.map_data import (
    apply_custom_weights,
    get_graph,
    get_node_coordinates,
    get_incidents_near_route,
    get_nearest_node,
)
from core.logic.route_planner import get_optimized_routes


def create_map(location: tuple[float, float], zoom_start: int = 12) -> folium.Map:
    """
    Crea un mapa centrado en una ubicación específica.

    Args:
        location (tuple): Coordenadas (lat, lon) donde se centrará el mapa.
        zoom_start (int): Nivel de zoom inicial.

    Returns:
        folium.Map: Mapa centrado en la ubicación.
    """
    return folium.Map(location=location, zoom_start=zoom_start)


def draw_route_on_map(
    map_obj: folium.Map,
    route_coords: list[tuple[float, float]],
    danger_level: float,
    color: str,
) -> None:
    """
    Dibuja una ruta sobre el mapa, con colores según su peligrosidad.

    Args:
        map_obj (folium.Map): El objeto del mapa de folium.
        route_coords (list): Lista de coordenadas [(lat1, lon1), (lat2, lon2), ...] que forman la ruta.
        danger_level (float): Peligrosidad de la ruta (valor entre 0 y 1).
        color (str): Color de la ruta según el nivel de peligro.

    Returns:
        None
    """
    folium.PolyLine(route_coords, color=color, weight=5, opacity=0.7).add_to(map_obj)


def add_incidents_markers(
    map_obj: folium.Map, route_coords: list[tuple[float, float]]
) -> None:
    """
    Agrega marcadores de incidentes con tamaño proporcional a su gravedad.

    Args:
        map_obj (folium.Map): El objeto del mapa de folium.
        route_coords (list): Lista de coordenadas de la ruta.

    Returns:
        None
    """
    incidents = get_incidents_near_route(route_coords)
    for inc in incidents:
        size = inc.gravedad * 3  # Escalando la gravedad para tamaño del marcador
        folium.CircleMarker(
            location=(inc.latitud, inc.longitud),
            radius=size,
            color="red",
            fill=True,
            fill_color="red",
            popup=f"Tipo: {inc.tipo}, Gravedad: {inc.gravedad}",
        ).add_to(map_obj)


def add_legend(map_obj: folium.Map) -> None:
    """
    Agrega una leyenda al mapa para indicar los niveles de peligro.

    Args:
        map_obj (folium.Map): El objeto del mapa de folium.

    Returns:
        None
    """
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 10px; 
        left: 10px; 
        width: 180px; 
        background-color: white; 
        z-index:9999; 
        padding: 10px; 
        font-size:14px;
        border: 1px solid black;">
        <b>Legendas de peligro</b><br>
        <i style="background:green;width:10px;height:10px;display:inline-block;"></i> Ruta Segura<br>
        <i style="background:orange;width:10px;height:10px;display:inline-block;"></i> Riesgo Medio<br>
        <i style="background:red;width:10px;height:10px;display:inline-block;"></i> Ruta Peligrosa<br>
        <i style="background:red;width:10px;height:10px;display:inline-block;border-radius:50%;"></i> Incidentes (Tamaño según gravedad)
    </div>
    """
    map_obj.get_root().html.add_child(folium.Element(legend_html))


def visualize_route_with_peligrosidad(
    place_name: str,
    origin_coords: tuple[float, float],
    dest_coords: tuple[float, float],
) -> folium.Map:
    """
    Visualiza múltiples rutas con diferentes niveles de seguridad y peligrosidad en un mapa interactivo.

    Args:
        place_name (str): Nombre del lugar.
        origin_coords (tuple): Coordenadas (lat, lon) del origen.
        dest_coords (tuple): Coordenadas (lat, lon) del destino.

    Returns:
        folium.Map: Mapa interactivo con rutas, incidentes y leyendas.
    """
    # Obtener el grafo del lugar
    graph = get_graph(place_name)

    # Obtener los nodos más cercanos al origen y destino
    origin_node = get_nearest_node(graph, origin_coords)
    dest_node = get_nearest_node(graph, dest_coords)

    # Crear el mapa centrado en las coordenadas de origen
    map_obj = create_map(origin_coords)

    # Generar rutas alternativas con diferentes pesos de seguridad
    weights = [0.6, 0.8, 1.0]  # Diferentes prioridades de seguridad
    colors = ["green", "orange", "red"]  # Colores según peligrosidad

    # Iterar sobre los pesos de seguridad y calcular las rutas
    for w_safety, color in zip(weights, colors):
        # Aplicar pesos personalizados al grafo
        graph_safe = apply_custom_weights(graph, w_safety)

        # Obtener las rutas optimizadas con los pesos de seguridad
        route_data = get_optimized_routes(graph_safe, origin_node, dest_node)

        # Obtener las coordenadas de la ruta
        route_coords = [
            get_node_coordinates(graph_safe, node) for node in route_data["ruta"]
        ]

        # Dibujar la ruta en el mapa
        draw_route_on_map(map_obj, route_coords, route_data["peligrosidad"], color)

    # Agregar marcadores de incidentes en el mapa
    add_incidents_markers(map_obj, route_coords)

    # Agregar leyenda de peligrosidad
    add_legend(map_obj)

    return map_obj
