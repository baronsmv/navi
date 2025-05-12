document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map').setView([20.1011, -98.7591], 13);
    initTileLayer(map);

    const resetBtn = document.getElementById('resetBtn');
    const dangerText = document.getElementById('danger');

    // Estado centralizado
    const mapState = {
        originCoords: null,
        destCoords: null,
        originMarker: null,
        destMarker: null,
        routeLine: null,
        incidentMarkers: []
    };

    resetBtn.addEventListener('click', () => resetMap(map, mapState, dangerText));

    // const incidents = getIncidents();
    // mapState.incidentMarkers = getMarkers(incidents, map);

    map.on('click', function (e) {
        const latlng = [e.latlng.lat, e.latlng.lng];

        if (!mapState.originCoords) {
            setOrigin(map, latlng, mapState);
        } else if (!mapState.destCoords) {
            setDestination(map, latlng, mapState);
            calculateRoute(map, mapState, dangerText);
        }
    });
});
