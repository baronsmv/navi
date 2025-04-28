# core.views.py

import json
import logging

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from core.forms import IncidentForm
from core.logic.route_danger import (
    calculate_combined_cost,
)
from core.logic.route_utils import (
    extract_route_coords,
    get_danger_level,
    get_incidents,
    get_route,
    get_graph,
    parse_coordinates,
)
from core.models import Incident

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "mapa.html")


def add_incident(request):
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


def prepare_incidents():
    incidents_qs = Incident.objects.exclude(latitude=0, longitude=0)
    incidents_data = tuple(
        {
            "lat": i.latitude,
            "lon": i.longitude,
            "severity": i.severity,
            "type": i.get_type_display(),
            "date": str(i.incident_date),
            "description": i.description or "Sin descripción",
        }
        for i in incidents_qs
    )
    return {"incidents": incidents_qs, "incidents_json": json.dumps(incidents_data)}


def incident_list(request):
    return render(
        request,
        "incident_list.html",
        prepare_incidents(),
    )


@csrf_exempt
def calculate_route(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        origin_lat, origin_lon, dest_lat, dest_lon = parse_coordinates(request.POST)
        origin = (origin_lat, origin_lon)
        destination = (dest_lat, dest_lon)

        logger.info(f"Origen: {origin}, Destino: {destination}")

        graph = get_graph(origin, destination)
        graph_with_cost = calculate_combined_cost(graph)

        route, origin_node, dest_node = get_route(
            graph, graph_with_cost, origin, destination
        )
        logger.info(f"Ruta óptima de {origin_node} a {dest_node}: {route}")

        route_coords = extract_route_coords(graph, route)
        logger.info(f"Coordenadas de la ruta: {route_coords}")

        danger_level = get_danger_level(origin_lat, origin_lon)
        logger.info(f"Nivel de peligro de la ruta: {danger_level}")

        incidents = get_incidents(origin_lat, origin_lon)
        logger.info(f"Incidentes de la ruta: {incidents}")

        return JsonResponse(
            {
                "route": route_coords,
                "dangerLevel": danger_level,
                # **prepare_incidents(),
                "incidents": incidents,
            }
        )

    except ValueError as e:
        logger.warning(f"Error de validación: {e}")
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Ocurrió un error: {e}", exc_info=True)
        return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)
