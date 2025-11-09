# core.views.py

import logging

import networkx as nx
import osmnx as ox
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from scripts.graph_loader import (
    save_dynamic_graph,
    find_graph_for_route,
    get_local_subgraph,
)
from .forms import IncidentForm
from .logic.graph import (
    parse_coordinates,
    estimate_radius,
    assign_edge_risks,
    get_incidents_in_graph,
)
from .logic.serialize import serialize_incidents, build_geojson

logger = logging.getLogger(__name__)


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "mapa.html")


def add_incident(request: HttpRequest) -> HttpResponse:
    form = IncidentForm()
    if request.method == "POST":
        form = IncidentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Incidente registrado exitosamente!")
            return redirect("add_incident")
        else:
            logger.error(f"Ocurrió un error al registrar el incidente.")
            messages.error(request, "Hubo un error al registrar el incidente.")

    return render(request, "incident_form.html", {"form": form})


def incident_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "incident_list.html",
        serialize_incidents(),
    )


@csrf_exempt
def calculate_route(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        origin_lat, origin_lon, dest_lat, dest_lon = parse_coordinates(
            request.POST
        )
        origin = (origin_lat, origin_lon)
        destination = (dest_lat, dest_lon)
        center = (
            (origin[0] + destination[0]) / 2,
            (origin[1] + destination[1]) / 2,
        )
        radius_m = estimate_radius(origin, destination)

        logger.info(f"Solicitando ruta de {origin} a {destination}")

        # Buscar grafo que contenga ambos puntos
        graph_path = find_graph_for_route(origin, destination)

        if graph_path:
            logger.info(f"✅ Usando grafo en caché: {graph_path.name}")
            graph = ox.load_graphml(graph_path)
        else:
            logger.info("📍 No se encontró grafo en caché. Descargando...")
            try:
                graph_path = save_dynamic_graph(center, radius_m)
                graph = ox.load_graphml(graph_path)
                logger.info(f"✅ Grafo dinámico guardado: {graph_path.name}")
            except Exception as e:
                logger.error(f"❌ Error al descargar grafo: {e}")
                return JsonResponse(
                    {
                        "error": "No se pudo obtener el grafo de la zona solicitada.",
                        "details": str(e),
                    },
                    status=503,
                )

        # Intentar recortar el grafo
        try:
            subgraph = get_local_subgraph(graph, origin, destination)

            # Verificar que ambos nodos estén en el subgrafo
            origin_node = ox.distance.nearest_nodes(
                subgraph, origin[1], origin[0]
            )
            dest_node = ox.distance.nearest_nodes(
                subgraph, destination[1], destination[0]
            )

            if (
                origin_node not in subgraph.nodes
                or dest_node not in subgraph.nodes
            ):
                logger.warning(
                    "⚠️ Subgrafo no contiene ambos nodos. Usando grafo completo."
                )
                subgraph = graph
                origin_node = ox.distance.nearest_nodes(
                    graph, origin[1], origin[0]
                )
                dest_node = ox.distance.nearest_nodes(
                    graph, destination[1], destination[0]
                )
        except Exception as e:
            logger.warning(
                f"⚠️ Error al recortar grafo: {e}. Usando grafo completo."
            )
            subgraph = graph
            origin_node = ox.distance.nearest_nodes(
                graph, origin[1], origin[0]
            )
            dest_node = ox.distance.nearest_nodes(
                graph, destination[1], destination[0]
            )

        # Asignar riesgos y calcular ruta
        incidents = get_incidents_in_graph(subgraph)
        assign_edge_risks(subgraph, incidents)

        logger.info(
            f"Subgrafo: {len(subgraph.nodes)} nodos, {len(subgraph.edges)} aristas"
        )
        logger.info(f"Nodo origen: {origin_node}, destino: {dest_node}")

        try:
            route = nx.dijkstra_path(
                subgraph, origin_node, dest_node, weight="combined_cost"
            )
        except nx.NetworkXNoPath:
            return JsonResponse(
                {
                    "route": None,
                    "dangerLevel": 0.0,
                    "geojson": None,
                    "message": "No se encontró una ruta segura entre los puntos.",
                }
            )

        route_coords = [
            (subgraph.nodes[n]["y"], subgraph.nodes[n]["x"]) for n in route
        ]
        risks = [
            subgraph[u][v][k].get("risk", 0.0)
            for u, v in zip(route[:-1], route[1:])
            for k in subgraph[u][v]
        ]
        danger_level = max(risks) if risks else 0.0
        geojson = build_geojson(route_coords, danger_level)

        return JsonResponse(
            {
                "route": route_coords,
                "dangerLevel": danger_level,
                "geojson": geojson,
            }
        )

    except Exception:
        logger.exception("Error inesperado al calcular la ruta")
        return JsonResponse(
            {"error": "Error interno del servidor"}, status=500
        )
