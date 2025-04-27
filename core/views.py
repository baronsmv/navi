# core.views.py

import logging

import osmnx as ox
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from geopy.distance import geodesic

from core.forms import IncidenteForm
from core.logic.route_danger import (
    calculate_combined_cost,
    find_optimal_route,
)
from core.models import Incidente

logger = logging.getLogger(__name__)


def home(request):
    return render(request, "mapa.html")


def add_incident(request):
    if request.method == "POST":
        form = IncidenteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Incidente registrado exitosamente!")
            return redirect("add_incident")
        else:
            messages.error(request, "Hubo un error al registrar el incidente.")
    else:
        form = IncidenteForm()

    return render(request, "incident_form.html", {"form": form})


def incident_list(request):
    incidentes = Incidente.objects.all()
    return render(request, "incident_list.html", {"incidentes": incidentes})


@csrf_exempt
def calculate_route(request):
    """
    Calcula la mejor ruta entre dos puntos considerando seguridad y distancia.
    Devuelve la ruta optimizada, el nivel de peligro y los incidentes cercanos en formato JSON.

    Args:
        request (HttpRequest): Solicitud con datos de origen y destino.

    Returns:
        JsonResponse: Datos de la ruta, peligrosidad y incidentes cercanos.
    """
    if request.method == "POST":
        try:
            # Desempaquetado y empaquetado de coordenadas desde la solicitud
            origin_lat, origin_lon, dest_lat, dest_lon = (
                float(request.POST.get(c))
                for c in ("origin_lat", "origin_lon", "dest_lat", "dest_lon")
            )
            origin = (origin_lat, origin_lon)
            destination = (dest_lat, dest_lon)
            distance_km = geodesic(origin, destination).km
            radio = min(distance_km, 70) * 1000
            mid_lat = (origin_lat + dest_lat) / 2
            mid_lon = (origin_lon + dest_lon) / 2

            logger.info(f"Origen: {origin}")
            logger.info(f"Destino: {destination}")
            logger.info(f"Distancia entre el origen y el destino: {distance_km} km")

            graph = ox.graph_from_point(
                (mid_lat, mid_lon), dist=radio, network_type="all"
            )
            graph_with_combined_cost = calculate_combined_cost(graph)
            logger.info(
                f"Grafo obtenido con: {len(graph.nodes)} nodos y {len(graph.edges)} aristas"
            )

            """# Conversión del grafo en coordenadas (lat, lon)
            graph_latlon = map_data.build_latlon_graph(graph)"""

            # Búsqueda de los nodos más cercanos a los puntos dados
            try:
                origin_node = ox.distance.nearest_nodes(graph, origin_lon, origin_lat)
                dest_node = ox.distance.nearest_nodes(graph, dest_lon, dest_lat)
                optimal_route = find_optimal_route(
                    graph_with_combined_cost, origin_node, dest_node
                )
            except Exception as e:
                logger.error(f"Ocurrió un error: {e}", exc_info=True)
                raise

            logger.info(f"Ruta óptima de {origin_node} a {dest_node}: {optimal_route}")

            # Obtener las coordenadas de la ruta
            route_coords = [
                (graph.nodes[node]["y"], graph.nodes[node]["x"])
                for node in optimal_route
            ]

            # Nivel de peligrosidad de la ruta (solo un ejemplo de cálculo)
            danger_level = calculate_route_risk(
                origin_lat, origin_lon, 500
            )  # Asumiendo función de cálculo del riesgo

            # Datos de los incidentes cercanos (esto dependerá de tu base de datos de incidentes)
            incidents = get_nearby_incidents(
                origin_lat, origin_lon, 500
            )  # Asumiendo una función para obtener los incidentes cercanos

            # Responder con los datos en formato JSON
            return JsonResponse(
                {
                    "route": route_coords,
                    "dangerLevel": danger_level,
                    "incidents": incidents,
                }
            )

            """if not origin_node or not dest_node:
                return JsonResponse(
                    {"error": "No se encontraron nodos válidos en el grafo"}, status=400
                )

            # Obtener la ruta más segura y su peligrosidad
            logger.info("Obteniendo la ruta más segura...")
            route_data = route_planner.get_optimized_routes(
                graph, origin_node, dest_node
            )

            if not route_data["ruta"]:
                return JsonResponse(
                    {"error": "No hay ruta disponible entre los puntos dados"},
                    status=404,
                )

            # Usar el grafo reproyectado para obtener coordenadas de cada nodo
            route_coords = [
                map_data.get_point_from_node(graph_latlon, node).coords[0][::-1]
                for node in route_data["ruta"]
            ]
            danger_level = route_data["peligrosidad"]

            # Filtrar incidentes recientes cerca de la ruta
            incidents = map_data.get_incidents_near_route(route_coords, meses_atras=6)

            # Serializar incidentes para el frontend con estructura más clara
            serialized_incidents = [
                {
                    "lat": inc.latitud,
                    "lon": inc.longitud,
                    "type": inc.tipo,
                    "severity": inc.gravedad,
                    "status": inc.estado,
                }
                for inc in incidents
            ]

            return JsonResponse(
                {
                    "route": route_coords,
                    "dangerLevel": danger_level,
                    "incidents": serialized_incidents,
                }
            )"""

            print("ACABADO " * 10, flush=True)
            return JsonResponse(
                {
                    "route": None,
                    "dangerLevel": None,
                    "incidents": None,
                }
            )

        except ValueError as e:
            return JsonResponse({"error": f"Error de validación: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
