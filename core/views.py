# core.views.py

import logging

import networkx as nx
import osmnx as ox
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse, HttpRequest
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

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

        logger.info(f"Solicitando ruta de {origin} a {destination}")

        radius_m = estimate_radius(origin, destination)
        center = (
            (origin[0] + destination[0]) / 2,
            (origin[1] + destination[1]) / 2,
        )
        graph = ox.graph_from_point(
            center, dist=radius_m, network_type="drive"
        )

        if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
            return JsonResponse(
                {"error": "No se pudo generar el grafo."}, status=500
            )

        incidents = get_incidents_in_graph(graph)
        assign_edge_risks(graph, incidents)

        try:
            origin_node = ox.distance.nearest_nodes(
                graph, origin[1], origin[0]
            )
            dest_node = ox.distance.nearest_nodes(
                graph, destination[1], destination[0]
            )
            route = nx.dijkstra_path(
                graph, origin_node, dest_node, weight="combined_cost"
            )
        except nx.NetworkXNoPath:
            logger.warning("No se encontró una ruta entre los puntos.")
            return JsonResponse(
                {
                    "route": None,
                    "dangerLevel": 0.0,
                    "geojson": None,
                    "message": "No se encontró una ruta segura entre los puntos.",
                }
            )

        route_coords = [
            (graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in route
        ]
        danger_level = max(
            graph[u][v][k].get("risk", 0.0)
            for u, v, k in zip(route[:-1], route[1:], [0] * len(route))
        )
        geojson = build_geojson(route_coords, danger_level)

        logger.info(
            f"Ruta generada con {len(route)} nodos y nivel de peligro {danger_level:.2f}"
        )

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
