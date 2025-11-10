from datetime import datetime, timedelta
from pathlib import Path

import osmnx as ox

from .config import (
    cache_locations,
    cache_max_age,
    cache_radius,
    PREBUILT_GRAPH_DIR,
)

ox.settings.use_cache = True
ox.settings.log_console = True


def is_recent(filepath: Path) -> bool:
    """Verifica si el archivo fue modificado hace menos de X días."""
    if not filepath.exists():
        return False
    modified = datetime.fromtimestamp(filepath.stat().st_mtime)
    return modified > datetime.now() - timedelta(days=cache_max_age)


for name, (lat, lon) in cache_locations.items():
    if not isinstance(lat, float) or not isinstance(lon, float):
        print(f"Latitud o longitud no válidas para {name}. Omitido.")
        continue

    filename = f"{name}.graphml"
    filepath = PREBUILT_GRAPH_DIR / filename

    if is_recent(filepath):
        print(f"Grafo reciente encontrado para {name}, omitido.")
        continue

    print(f"Generando grafo para {name}...")
    try:
        graph = ox.graph_from_point(
            (lat, lon), dist=cache_radius, network_type="drive"
        )
        ox.save_graphml(graph, filepath)
        print(f"Grafo guardado: {filename}")
    except Exception as e:
        print(f"Error al generar grafo para {name}: {e}")
