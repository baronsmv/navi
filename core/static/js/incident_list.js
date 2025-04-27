document.addEventListener("DOMContentLoaded", function () {
    console.log(L);
    const map = L.map('map');
    initTileLayer(map);

    const incidents = getIncidents();
    const markers = getMarkers(incidents, map);

    setupMarkerClickHandlers(markers, map);
    setupTableClickHandlers(markers, map);
});
