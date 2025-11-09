from datetime import datetime, timedelta
from pathlib import Path

import environ
import osmnx as ox

# Load environment
BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env()
env.read_env(BASE_DIR / ".env")

# OSMnx settings
ox.settings.use_cache = True
ox.settings.log_console = True

# Output directory for prebuilt graphs
output_dir = BASE_DIR / "cache" / "graphs" / "prebuilt"
output_dir.mkdir(parents=True, exist_ok=True)

# Config
locations = env.list("GRAPH_LOCATIONS", default=[])
radius = env.int("GRAPH_RADIUS", default=5000)
max_age_days = 7
cutoff = datetime.now() - timedelta(days=max_age_days)


def is_recent(filepath: Path) -> bool:
    """Verifica si el archivo fue modificado hace menos de X días."""
    if not filepath.exists():
        return False
    modified = datetime.fromtimestamp(filepath.stat().st_mtime)
    return modified > cutoff


for name in locations:
    coord_str = env.str(f"GRAPH_{name}", default=None)
    if not coord_str:
        print(f"Coordenadas no definidas para {name}")
        continue

    lat, lon = map(float, coord_str.split(","))
    filename = f"{name}.graphml"
    filepath = output_dir / filename

    if is_recent(filepath):
        print(f"Grafo reciente encontrado para {name}, omitido.")
        continue

    print(f"Generando grafo para {name}...")
    try:
        graph = ox.graph_from_point(
            (lat, lon), dist=radius, network_type="drive"
        )
        ox.save_graphml(graph, filepath)
        print(f"Grafo guardado: {filename}")
    except Exception as e:
        print(f"Error al generar grafo para {name}: {e}")
