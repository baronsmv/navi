from pathlib import Path
from typing import Dict, List

import yaml


def load_config(path: Path) -> Dict[str, Dict]:
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
GRAPH_DIR = BASE_DIR / "cache" / "graphs"
PREBUILT_GRAPH_DIR = GRAPH_DIR / "prebuilt"
DYNAMIC_GRAPH_DIR = GRAPH_DIR / "dynamic"

for dir in (PREBUILT_GRAPH_DIR, DYNAMIC_GRAPH_DIR):
    dir.mkdir(parents=True, exist_ok=True)

CONFIG = load_config(CONFIG_PATH)

# Categorías de configuración
risk: Dict[str, Dict] = CONFIG.get("risk", {})
incidents: Dict[str, Dict] = CONFIG.get("incidents", {})
graph_cache: Dict[str, Dict] = CONFIG.get("graph_cache", {})

# Datos de caché de grafos
cache_locations: Dict[str, List[float]] = graph_cache.get("locations", {})
cache_radius = graph_cache.get("radius", 10000)
cache_max_age = graph_cache.get("max_age", 7)
