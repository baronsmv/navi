function highlightRow(index) {
    document.querySelectorAll("tr[data-index]").forEach(row => {
        row.classList.remove("highlight");
    });

    const row = document.querySelector(`tr[data-index='${index}']`);
    if (row) {
        row.classList.add("highlight");
        row.scrollIntoView({behavior: "smooth", block: "center"});
    }
}

function setupTableClickHandlers(markers, map) {
    document.querySelectorAll("tr[data-index]").forEach(row => {
        row.addEventListener("click", () => {
            const index = parseInt(row.dataset.index);
            const marker = markers[index];

            // Center the map on the marker and open its popup
            const latlng = marker.getLatLng();
            map.flyTo(latlng, 13, {animate: true});
            marker.openPopup();

            highlightRow(index);
        });
    });
}
