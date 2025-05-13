function getIncidents() {
    const dataContainer = document.getElementById("incident-data");
    if (!dataContainer || !dataContainer.dataset.incidents) {
        console.error("No incidents data found.");
        return [];
    }
    const incidentsData = dataContainer.dataset.incidents;
    console.log("Incidents data: ", incidentsData);
    try {
        return JSON.parse(incidentsData); // Parse the JSON data
    } catch (error) {
        console.error("Failed to parse incidents data:", error);
        return [];
    }
}

function createIncidentMarker(incident) {
    const markerColor = getColor(incident.severity, [0, 1, 2, 3, 4, 5]);
    return L.circleMarker([incident.lat, incident.lon], {
        color: markerColor,
        fillColor: markerColor,
        fillOpacity: 0.6,
        radius: 8
    }).bindPopup(`<b>${incident.type}<br>${incident.date}</b><br>${incident.description}`);
}

function getMarkers(incidents, map) {
    if (Array.isArray(incidents) && incidents.length > 0) {
        const markerGroup = L.featureGroup();
        const markers = [];

        incidents.forEach(incident => {
            const marker = createIncidentMarker(incident);
            markerGroup.addLayer(marker);
            markers.push(marker);
        });

        markerGroup.addTo(map);
        map.fitBounds(markerGroup.getBounds(), {padding: [30, 30]});
        return markers;
    } else {
        map.setView([19.4326, -99.1332], 6); // Fallback to CDMX (Mexico City)
        return [];
    }
}

function handleMarkerClick(marker, map, index) {
    const latlng = marker.getLatLng();
    map.flyTo(latlng, 15, {animate: true});
    highlightRow(index);
}

function setupMarkerClickHandlers(markers, map) {
    markers.forEach((marker, index) => {
        marker.on('click', () => {
            handleMarkerClick(marker, map, index);
        });
    });
}
