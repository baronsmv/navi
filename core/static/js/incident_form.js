document.addEventListener("DOMContentLoaded", function () {
    // Crea un mapa centrado en una ubicación por defecto (por ejemplo, Ciudad de México)
    var map = L.map('map').setView([19.4326, -99.1332], 13);  // Valor por defecto (CDMX)

    // Añadir capa de OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Añadir un marcador inicial en el centro del mapa
    var marker = L.marker([19.4326, -99.1332], { draggable: true }).addTo(map);

    // Actualiza los campos del formulario con las coordenadas del marcador
    function updateFormCoordinates(lat, lon) {
        // Actualiza los valores de los campos de latitud y longitud
        document.getElementById('id_latitud').value = lat;
        document.getElementById('id_longitud').value = lon;
    }

    // Si la geolocalización está disponible, intenta obtener la ubicación del usuario
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function (position) {
            var userLat = position.coords.latitude;
            var userLon = position.coords.longitude;

            // Centra el mapa en la ubicación del usuario y coloca el marcador allí
            map.setView([userLat, userLon], 13);
            marker.setLatLng([userLat, userLon]);

            // Actualiza los campos del formulario con la ubicación del usuario
            updateFormCoordinates(userLat, userLon);
        }, function (error) {
            console.log("Error al obtener la ubicación: " + error.message);
        });
    } else {
        console.log("Geolocalización no soportada en este navegador.");
    }

    // Evento: cuando el usuario hace clic en el mapa, mueve el marcador a esa posición
    map.on('click', function (e) {
        // Obtiene las coordenadas del clic
        var lat = e.latlng.lat;
        var lon = e.latlng.lng;

        // Mueve el marcador a la nueva posición
        marker.setLatLng([lat, lon]);

        // Actualiza los campos de latitud y longitud del formulario
        updateFormCoordinates(lat, lon);
    });

    // También puedes permitir que el marcador sea arrastrable, lo que actualizará la posición
    marker.on('dragend', function (e) {
        var lat = e.target.getLatLng().lat;
        var lon = e.target.getLatLng().lng;

        // Actualiza los campos del formulario con la nueva posición del marcador
        updateFormCoordinates(lat, lon);
    });
});
