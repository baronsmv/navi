function initTileLayer(map) {
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        detectRetina: true,
    }).addTo(map);
}

function getColor(severity, domain) {
    const scale = d3.scaleLinear()
        .domain(domain)  // Usa el dominio pasado como argumento
        .range(['green', 'yellow', 'orange', 'red', 'darkred']); // Color range

    return scale(severity);
}