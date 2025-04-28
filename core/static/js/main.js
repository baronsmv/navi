const map = L.map('map').setView([20.1011, -98.7591], 13); // Pachuca

initTileLayer(map);

let originMarker, destMarker, routeLine, incidentMarkers = [];
let originCoords = null;
let destCoords = null;

map.on('click', function (e) {
    if (!originCoords) {
        originCoords = [e.latlng.lat, e.latlng.lng];
        originMarker = L.marker(originCoords).addTo(map)
            .bindPopup("Origen").openPopup();
    } else if (!destCoords) {
        destCoords = [e.latlng.lat, e.latlng.lng];
        destMarker = L.marker(destCoords).addTo(map)
            .bindPopup("Destino").openPopup();
        calculateRoute();
    }
});

document.getElementById('resetBtn').addEventListener('click', () => {
    if (originMarker) map.removeLayer(originMarker);
    if (destMarker) map.removeLayer(destMarker);
    if (routeLine) map.removeLayer(routeLine);
    incidentMarkers.forEach(m => map.removeLayer(m));
    incidentMarkers = [];
    originCoords = destCoords = null;
    document.getElementById('danger').innerText = "Nivel de peligrosidad: --";
});
