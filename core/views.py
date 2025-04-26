import osmnx as ox
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from core.forms import IncidenteForm
from core.logic import map_data, route_planner
from core.logic.map_visualizer import visualize_route_with_peligrosidad
from core.models import Incidente


def map_view(request):
    place_name = "Pachuca, Hidalgo, Mexico"
    origin_coords = (20.12, -98.74)
    dest_coords = (20.13, -98.75)

    map_object = visualize_route_with_peligrosidad(
        place_name, origin_coords, dest_coords
    )
    map_html = map_object._repr_html_()  # Convertir el objeto Folium a HTML

    return render(request, "map_template.html", {"map": map_html})


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
def calculate_route(request, debug: bool = True):
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
            # Obtener coordenadas desde la solicitud
            origin_lat = float(request.POST.get("origin_lat"))
            origin_lon = float(request.POST.get("origin_lon"))
            dest_lat = float(request.POST.get("dest_lat"))
            dest_lon = float(request.POST.get("dest_lon"))

            if debug:
                print(f"Origen: {origin_lat}, {origin_lon}", flush=True)
                print(f"Destino: {dest_lat}, {dest_lon}", flush=True)

            # Obtener el grafo de calles y aplicar los pesos de seguridad y distancia
            graph = map_data.get_graph("Pachuca, Hidalgo, Mexico")
            if debug:
                print(
                    f"Grafo cargado con {len(graph.nodes)} nodos y {len(graph.edges)} aristas",
                    flush=True,
                )
                print(
                    f"Ejemplo de nodos en el grafo: {list(graph.nodes)[:5]}", flush=True
                )
                print(
                    f"Ejemplo de aristas en el grafo: {list(graph.edges(data=True))[:5]}",
                    flush=True,
                )

            graph = map_data.apply_custom_weights(graph)  # Aplicar ponderación
            if debug:
                print(
                    f"Grafo después de ponderación: {len(graph.nodes)} nodos y {len(graph.edges)} aristas",
                    flush=True,
                )
                print(f"Nodos: {graph.nodes}")

            # Reproyectar a lat/lon para obtener nodos correctamente
            graph_latlon = map_data.build_latlon_graph(graph)

            # Encontrar los nodos más cercanos a los puntos dados
            origin_node = ox.distance.nearest_nodes(
                graph_latlon, origin_lon, origin_lat
            )
            dest_node = ox.distance.nearest_nodes(graph_latlon, dest_lon, dest_lat)

            if debug:
                print(f"Nodo origen: {origin_node}, Nodo destino: {dest_node}")

            if not origin_node or not dest_node:
                return JsonResponse(
                    {"error": "No se encontraron nodos válidos en el grafo"}, status=400
                )

            # Obtener la ruta más segura y su peligrosidad
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
            )

        except ValueError as e:
            return JsonResponse({"error": f"Error de validación: {str(e)}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error inesperado: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)
