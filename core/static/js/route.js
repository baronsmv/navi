function getRouteColor(level) {
    if (level < 3) return 'green';
    if (level < 6) return 'orange';
    return 'red';
}

function getIncidentColor(tipo) {
    switch (tipo.toLowerCase()) {
        case 'asalto':
            return '#e67e22'; // naranja
        case 'homicidio':
            return '#c0392b'; // rojo
        case 'accidente':
            return '#2980b9'; // azul
        default:
            return '#7f8c8d'; // gris
    }
}

function calculateRoute() {
    const data = new FormData();
    data.append('origin_lat', originCoords[0]);
    data.append('origin_lon', originCoords[1]);
    data.append('dest_lat', destCoords[0]);
    data.append('dest_lon', destCoords[1]);

    fetch('/calculate_route/', {
        method: 'POST',
        body: data
    })
        .then(response => response.json())
        .then(data => {
            if (data.route) {
                if (routeLine) map.removeLayer(routeLine);
                routeLine = L.polyline(data.route, {
                    color: getRouteColor(data.dangerLevel),
                    weight: 6
                }).addTo(map);
                map.fitBounds(routeLine.getBounds());

                document.getElementById('danger').innerText =
                    `Nivel de peligrosidad: ${data.dangerLevel.toFixed(2)}`;

                // Limpiar marcadores anteriores
                incidentMarkers.forEach(m => map.removeLayer(m));
                incidentMarkers = [];

                if (data.incidents) {
                    data.incidents.forEach(incident => {
                        const marker = L.circleMarker([incident.latitude, incident.longitude], {
                            radius: 6,
                            fillColor: getIncidentColor(incident.tipo),
                            color: '#333',
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.8
                        }).addTo(map).bindPopup(`
                        <strong>Tipo:</strong> ${incident.tipo}<br>
                        <strong>Gravedad:</strong> ${incident.gravedad}/5<br>
                        <strong>Estado:</strong> ${incident.estado}
                    `);
                        incidentMarkers.push(marker);
                    });
                }

            } else {
                alert("No se pudo calcular la ruta.");
            }
        })
        .catch(error => {
            console.error("Error:", error);
        });
}