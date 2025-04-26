from unittest import mock

import pytest
from django.http import JsonResponse

from core.views import calculate_route


@pytest.fixture
def mock_request():
    """Simula una solicitud POST con coordenadas de origen y destino."""

    class MockRequest:
        method = "POST"
        POST = {
            "origin_lat": "19.173",
            "origin_lon": "-98.203",
            "dest_lat": "19.143",
            "dest_lon": "-98.213",
        }

    return MockRequest()


def test_calculate_route(mock_request):
    """Prueba la función calculate_route."""

    # Mock de las funciones que se llaman dentro de calculate_route
    with mock.patch("map_data.get_graph") as mock_get_graph, mock.patch(
        "map_data.apply_custom_weights"
    ) as mock_apply_custom_weights, mock.patch(
        "map_data.build_latlon_graph"
    ) as mock_build_latlon_graph, mock.patch(
        "ox.distance.nearest_nodes"
    ) as mock_nearest_nodes, mock.patch(
        "route_planner.get_optimized_routes"
    ) as mock_get_optimized_routes, mock.patch(
        "map_data.get_incidents_near_route"
    ) as mock_get_incidents_near_route:
        # Configura los valores de retorno del mock
        mock_get_graph.return_value = (
            "graph_object"  # Esto puede ser un objeto de grafo de prueba
        )
        mock_apply_custom_weights.return_value = "graph_with_weights"
        mock_build_latlon_graph.return_value = "graph_latlon"
        mock_nearest_nodes.side_effect = [1, 2]  # Nodo origen y destino
        mock_get_optimized_routes.return_value = {
            "ruta": [1, 2, 3],
            "peligrosidad": 0.8,
        }
        mock_get_incidents_near_route.return_value = [
            mock.Mock(
                latitud=19.170,
                longitud=-98.205,
                tipo="Accidente",
                gravedad=3,
                estado="Nuevo",
            )
        ]

        # Llamar a la vista con la solicitud simulada
        response = calculate_route(mock_request)

        # Verificar que la respuesta es un JsonResponse
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        # Verificar que la ruta devuelta contiene las coordenadas correctas
        response_data = response.json()
        assert "route" in response_data
        assert response_data["route"] == [
            (19.173, -98.203),
            (19.143, -98.213),
            (19.173, -98.205),
        ]

        # Verificar el nivel de peligrosidad
        assert "dangerLevel" in response_data
        assert response_data["dangerLevel"] == 0.8

        # Verificar que los incidentes están correctamente serializados
        assert "incidents" in response_data
        assert len(response_data["incidents"]) > 0
        incident = response_data["incidents"][0]
        assert incident["lat"] == 19.170
        assert incident["lon"] == -98.205
        assert incident["type"] == "Accidente"
        assert incident["severity"] == 3
        assert incident["status"] == "Nuevo"
