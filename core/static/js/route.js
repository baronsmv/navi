// === Utilidades ===

function getRouteColor(level) {
    if (level < 3) return 'green';
    if (level < 6) return 'orange';
    return 'red';
}

function getIncidentColor(tipo) {
    switch (tipo.toLowerCase()) {
        case 'asalto':
            return '#e67e22';
        case 'homicidio':
            return '#c0392b';
        case 'accidente':
            return '#2980b9';
        default:
            return '#7f8c8d';
    }
}

// === Funciones de manejo de mapa ===

function setOrigin(map, latlng, state) {
    state.originCoords = latlng;
    if (state.originMarker) map.removeLayer(state.originMarker);

    state.originMarker = L.marker(latlng)
        .addTo(map)
        .bindPopup("Origen")
        .openPopup();
}

function setDestination(map, latlng, state) {
    state.destCoords = latlng;
    if (state.destMarker) map.removeLayer(state.destMarker);

    state.destMarker = L.marker(latlng)
        .addTo(map)
        .bindPopup("Destino")
        .openPopup();
}

function removeMarker(map, marker) {
    if (marker) map.removeLayer(marker);
}

function removeIncidentMarkers(map, state) {
    state.incidentMarkers.forEach(marker => map.removeLayer(marker));
    state.incidentMarkers = [];
}

function resetMap(map, state, dangerTextEl) {
    removeMarker(map, state.originMarker);
    removeMarker(map, state.destMarker);

    if (state.routeLine) {
        map.removeLayer(state.routeLine);
        state.routeLine = null;
    }

    removeIncidentMarkers(map, state);

    state.originCoords = null;
    state.destCoords = null;

    dangerTextEl.innerText = "Nivel de peligrosidad: --";
}

function calculateRoute(map, state, dangerTextEl) {
    const {originCoords, destCoords} = state;
    if (!originCoords || !destCoords) return;

    const formData = new FormData();
    formData.append('origin_lat', originCoords[0]);
    formData.append('origin_lon', originCoords[1]);
    formData.append('dest_lat', destCoords[0]);
    formData.append('dest_lon', destCoords[1]);

    fetch('/calculate_route/', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (!data.route) {
                alert("No se pudo calcular la ruta.");
                return;
            }

            if (state.routeLine) map.removeLayer(state.routeLine);

            state.routeLine = L.polyline(data.route, {
                color: getRouteColor(data.dangerLevel),
                weight: 6
            }).addTo(map);

            map.fitBounds(state.routeLine.getBounds());
            dangerTextEl.innerText = `Nivel de peligrosidad: ${data.dangerLevel.toFixed(2)}`;

            removeIncidentMarkers(map, state);

            if (Array.isArray(data.incidents)) {
                data.incidents.forEach(incident => {
                    const marker = L.circleMarker([incident.latitude, incident.longitude], {
                        radius: 6,
                        fillColor: getIncidentColor(incident.tipo),
                        color: '#333',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    })
                        .addTo(map)
                        .bindPopup(`
                    <strong>Tipo:</strong> ${incident.tipo}<br>
                    <strong>Gravedad:</strong> ${incident.gravedad}/5<br>
                    <strong>Estado:</strong> ${incident.estado}
                `);

                    state.incidentMarkers.push(marker);
                });
            }
        })
        .catch(error => {
            console.error("Error al calcular ruta:", error);
        });
}
