# core.views.py

import logging

import networkx as nx
import osmnx as ox
from django.contrib import messages
from django.contrib.gis.geos import Polygon, Point
from django.contrib.gis.measure import D
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import geodesic

from utils import serialize
from .forms import IncidentForm
from .logic.fuzzy_logic import calculate_fuzzy_danger
from .logic.route_utils import (
    parse_coordinates,
)
from .models import Incident

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
        serialize.incidents(),
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

        # Estimate radius based on distance
        distance_km = geodesic(origin, destination).km
        radius_m = min(max(distance_km * 1000 * 1.5, 1000), 3000)

        # Build graph
        graph = ox.graph_from_point(
            (
                (origin[0] + destination[0]) / 2,
                (origin[1] + destination[1]) / 2,
            ),
            dist=radius_m,
            network_type="drive",
        )

        if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
            return JsonResponse(
                {"error": "No se pudo generar el grafo."}, status=500
            )

        # Get bounding box for incident query
        nodes = list(graph.nodes(data=True))
        lats = [n[1]["y"] for n in nodes]
        lons = [n[1]["x"] for n in nodes]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        # Query incidents once
        bbox = Polygon.from_bbox((min_lon, min_lat, max_lon, max_lat))
        incidents = Incident.objects.filter(location__within=bbox)

        # Assign edge risk and cost
        speed = 50 / 3.6
        for u, v, k, data in graph.edges(keys=True, data=True):
            try:
                u_lat, u_lon = graph.nodes[u]["y"], graph.nodes[u]["x"]
                v_lat, v_lon = graph.nodes[v]["y"], graph.nodes[v]["x"]
                midpoint = Point(
                    (u_lon + v_lon) / 2, (u_lat + v_lat) / 2, srid=4326
                )

                data["length"] = geodesic(
                    (u_lat, u_lon), (v_lat, v_lon)
                ).meters
                nearby = incidents.filter(
                    location__distance_lte=(midpoint, D(m=50))
                )

                if nearby:
                    avg_severity = sum(i.severity for i in nearby) / len(
                        nearby
                    )
                    days = [
                        (now().date() - i.incident_date).days for i in nearby
                    ]
                    avg_time = sum(days) / len(days)
                    risk = calculate_fuzzy_danger(
                        len(nearby), avg_severity, 50, avg_time
                    )
                else:
                    risk = 0.0

                time = data["length"] / speed
                data["risk"] = risk
                data["combined_cost"] = (risk * 0.7) + (time * 0.3)

            except Exception:
                data["length"] = 1.0
                data["risk"] = 0.0
                data["combined_cost"] = 1.0

        # Route
        origin_node = ox.distance.nearest_nodes(graph, origin[1], origin[0])
        dest_node = ox.distance.nearest_nodes(
            graph, destination[1], destination[0]
        )
        route = nx.dijkstra_path(
            graph, origin_node, dest_node, weight="combined_cost"
        )

        coords = [(graph.nodes[n]["y"], graph.nodes[n]["x"]) for n in route]
        danger = max(
            graph[u][v][k].get("risk", 0.0)
            for u, v, k in zip(route[:-1], route[1:], [0] * len(route))
        )

        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [(lon, lat) for lat, lon in coords],
            },
            "properties": {"dangerLevel": danger},
        }

        return JsonResponse(
            {"route": coords, "dangerLevel": danger, "geojson": geojson}
        )

    except Exception:
        logger.exception("Error inesperado al calcular la ruta")
        return JsonResponse(
            {"error": "Error interno del servidor"}, status=500
        )
