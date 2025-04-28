// Configuración inicial del mapa
const map = L.map('map').setView([20.1011, -98.7591], 13); // Pachuca
initTileLayer(map);

let originMarker, destMarker, routeLine;
let incidentMarkers = [];
let originCoords = null, destCoords = null;

// Elementos del DOM
const resetBtn = document.getElementById('resetBtn');
const dangerText = document.getElementById('danger');

// Función para reiniciar el mapa
resetBtn.addEventListener('click', resetMap);

// Función para manejar clics en el mapa
map.on('click', function (e) {
    const latlng = [e.latlng.lat, e.latlng.lng];

    if (!originCoords) {
        setOrigin(latlng);
    } else if (!destCoords) {
        setDestination(latlng);
        calculateRoute();
    }
});
