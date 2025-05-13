// === Utilidades ===

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

function updateDangerLevel(dangerTextEl, dangerLevel) {
    dangerTextEl.innerText = `Nivel de peligrosidad: ${dangerLevel.toFixed(2)}`;
}

function getColor(severity, domain) {
    const scale = d3.scaleLinear()
        .domain(domain)  // Usa el dominio pasado como argumento
        .range(['green', 'yellow', 'orange', 'red', 'darkred']); // Color range

    return scale(severity);
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

            // Verifica el valor de 'dangerLevel' que llega en la respuesta
            console.log('Nivel de peligrosidad:', data.dangerLevel);
            console.log('Incidentes:', data.incidents);

            // Eliminar la ruta anterior, si existe
            if (state.routeLine) map.removeLayer(state.routeLine);

            // Obtener el color de la ruta según el nivel de peligro
            const routeColor = getColor(data.dangerLevel, [0, 0.2, 0.4, 0.6, 0.8, 1]);

            console.log('Color de la ruta:', routeColor); // Verifica el color calculado

            // Crear la nueva línea de ruta con el color correspondiente
            state.routeLine = L.polyline(data.route, {
                color: routeColor,  // Asignamos el color basado en el nivel de peligro
                weight: 6
            }).addTo(map);

            // Ajustamos el mapa a la nueva ruta
            map.fitBounds(state.routeLine.getBounds());

            // Actualizar el nivel de peligro
            updateDangerLevel(dangerTextEl, data.dangerLevel);

            // Graficar los incidentes
            if (data.incidents && Array.isArray(data.incidents) && data.incidents.length > 0) {
                getMarkers(data.incidents, map);
            } else {
                console.log("No hay incidentes para mostrar.");
            }
        })
        .catch(error => {
            console.error("Error al calcular ruta:", error);
        });
}

