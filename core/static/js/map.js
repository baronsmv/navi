document.addEventListener('DOMContentLoaded', () => {
    const map = L.map('map', {zoomControl: false}).setView([20.1011, -98.7591], 13);
    L.control.zoom({position: 'bottomright'}).addTo(map);
    initTileLayer(map);
    const resetBtn = document.getElementById('resetBtn');
    const dangerText = document.getElementById('danger');

    // Slider
    const securitySlider = document.getElementById("securitySlider");
    const securityValue = document.getElementById("securityValue");

    securitySlider.addEventListener("input", () => {
        const label = getSecurityLabel(securitySlider.value);
        securityValue.textContent = label;
    });

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
