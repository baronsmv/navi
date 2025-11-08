# core.views.py

import logging

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from utils import serialize
from .forms import IncidentForm
from .logic.route_danger import (
    route_risk,
    route_incidents,
)
from .logic.route_utils import (
    extract_route_coords,
    get_route,
    get_graph,
    parse_coordinates,
)

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
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        origin_lat, origin_lon, dest_lat, dest_lon = parse_coordinates(request.POST)
        origin = (origin_lat, origin_lon)
        destination = (dest_lat, dest_lon)

        logger.info(f"Origen: {origin}, Destino: {destination}")

        graph = get_graph(origin, destination)

        # Validar que el grafo tenga nodos y aristas
        if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
            logger.error("El grafo generado está vacío.")
            return JsonResponse(
                {"error": "No se pudo generar el grafo de navegación."}, status=500
            )

        # Obtener la mejor ruta
        route, origin_node, dest_node = get_route(graph, graph, origin, destination)

        if not route:
            logger.warning("No se encontró una ruta óptima.")
            return JsonResponse(
                {
                    "route": [],
                    "dangerLevel": 0.0,
                    "incidents": [],
                    "message": "No se encontró una ruta óptima.",
                }
            )

        logger.info(f"Ruta óptima de {origin_node} a {dest_node}: {route}")

        route_coords = extract_route_coords(graph, route)
        logger.info(f"Coordenadas de la ruta: {route_coords}")

        # Solo calcular peligrosidad si la ruta es válida
        incidents = route_incidents(graph, route)
        logger.info(f"Incidentes de la ruta: {incidents}")

        danger_level = route_risk(incidents, graph, route)
        logger.info(f"Nivel de peligro de la ruta: {danger_level}")

        return JsonResponse(
            {
                "route": route_coords,
                "dangerLevel": danger_level,
                "incidents": serialize.incidents(incidents, False)["incidents_json"],
            }
        )

    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        return JsonResponse({"error": str(e)}, status=400)

    except Exception as e:
        logger.error(f"Ocurrió un error inesperado: {e}", exc_info=True)
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)
