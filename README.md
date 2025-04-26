# navi

A safety-oriented navigation app.

## Estructura del proyecto

```txt
navi/
│
├── navi/           # Configuración principal de Django (settings, urls, etc.)
│   ├── asgi.py
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/                      # App principal del sistema de navegación
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py              # Datos de rutas, puntos, usuarios, etc.
│   ├── views.py               # Manejo de peticiones y respuestas HTTP
│   ├── urls.py
│   ├── templates/
│   │   └── core/
│   │       └── mapa.html      # Vista donde se renderiza el mapa con Folium
│   ├── static/
│   │   └── core/              # Archivos estáticos (CSS y JS)
│   ├── forms.py               # Formularios de búsqueda de rutas
│   └── logic/                 # Lógica personalizada para rutas e IA
│       ├── __init__.py
│       ├── map_data.py        # Carga de datos OSM con osmnx/overpy
│       ├── route_planner.py   # Planificación de rutas con NetworkX
│       ├── fuzzy_logic.py     # Evaluación fuzzy con skfuzzy
│       └── map_visualizer.py  # Generación de mapas con Folium
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## Detalle de cada módulo

### `map_data.py`

- Uso de `osmnx` y/o `overpy` para obtener los datos de calles, nodos, puntos de interés.
- Ejemplo: descarga de red de calles de una ciudad.

### `route_planner.py`

- Uso de `networkx` para crear el grafo y calcular rutas.
- Funciones como:
  - `get_shortest_path()`
  - `get_alternative_paths()`

### `fuzzy_logic.py`

- Uso de `skfuzzy` para calcular "calidad" o "confortabilidad" de una ruta, o para tomar decisiones basadas en múltiples factores (tráfico, seguridad, tiempo, etc.).
- Funciones como:
  - `evaluate_route_quality(route_info)`

### `map_visualizer.py`

- Uso de `folium` para renderizar mapas interactivos con rutas dibujadas.
- Funciones como:
  - `create_map_with_route()`

---

## Flujo típico (vista web)

1. El usuario selecciona una ubicación de origen y destino.
2. Django recibe la petición vía `views.py`.
3. Se llama a:
   - `map_data.py` para cargar/red procesar datos de la zona.
   - `route_planner.py` para calcular la(s) ruta(s).
   - `fuzzy_logic.py` para evaluar cuál es mejor.
   - `map_visualizer.py` para generar un mapa interactivo.
4. La vista renderiza el resultado en una plantilla HTML.

---

## Tips útiles

- Usa **caché** o almacenamiento intermedio para no volver a descargar/redibujar datos de OSM cada vez.
- Considera usar **GeoDjango** si planeas hacer consultas espaciales más complejas.
- Puedes integrar **AJAX** para mejorar la experiencia del usuario al buscar rutas sin recargar la página.
