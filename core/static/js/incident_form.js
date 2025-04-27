document.addEventListener("DOMContentLoaded", function () {
    function updateFormCoordinates(lat, lon) {
        console.log("Actualizando coords:", lat, lon);
        document.getElementById('id_latitud').value = lat;
        document.getElementById('id_longitud').value = lon;
    }

    // Definimos mapa y marcador como variables globales dentro de la función para usarlas luego
    function initMap(lat, lon) {
        const map = L.map('map').setView([lat, lon], 15);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        const marker = L.marker([lat, lon], { draggable: true }).addTo(map);

        updateFormCoordinates(lat, lon);

        map.on('click', function (e) {
            const { lat, lng } = e.latlng;
            marker.setLatLng([lat, lng]);
            updateFormCoordinates(lat, lng);
        });

        marker.on('dragend', function (e) {
            const { lat, lng } = e.target.getLatLng();
            updateFormCoordinates(lat, lng);
        });
    }

    // Intenta usar la ubicación del usuario
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            function (position) {
                const userLat = position.coords.latitude;
                const userLon = position.coords.longitude;
                initMap(userLat, userLon);
            },
            function (error) {
                console.warn("No se pudo obtener la ubicación. Usando CDMX.");
                initMap(19.4326, -99.1332);  // fallback CDMX
            }
        );
    } else {
        console.warn("Geolocalización no soportada. Usando CDMX.");
        initMap(19.4326, -99.1332);
    }
});
