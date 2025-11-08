import logging
from itertools import product

import skfuzzy as fuzz
import skfuzzy.control as ctrl
from numpy import ndarray, arange

logger = logging.getLogger(__name__)


def create_fuzzy_variable(
    name: str, universe: ndarray, membership: dict, is_consequent: bool = False
) -> ctrl.Antecedent | ctrl.Consequent:
    """
    Crea una variable difusa con funciones de pertenencia.

    Args:
        name: Nombre de la variable.
        universe: Rango de valores posibles (universo de discurso).
        membership: Diccionario con funciones de pertenencia.
        is_consequent: Es consecuente o, en su defecto, antecedente.

    Returns:
        Variable difusa configurada.
    """
    variable = (
        ctrl.Consequent(universe, name)
        if is_consequent
        else ctrl.Antecedent(universe, name)
    )

    # Aplicación de funciones de membresía
    for label, values in membership.items():
        variable[label] = fuzz.gbellmf(variable.universe, *values)

    return variable


def build_fuzzy_system() -> ctrl.ControlSystem:
    """
    Crea el sistema difuso para evaluar la peligrosidad de una ruta.

    Returns:
        Sistema difuso.
    """
    # Universos de valores
    incidents_universe = arange(0, 51, 1)  # Número de incidentes cercanos
    gravity_universe = arange(1, 5.1, 0.1)  # Gravedad de los incidentes (1-5)
    risk_zone_universe = arange(0, 101, 1)  # Distancia a zona de riesgo (0-100 metros)
    time_universe = arange(0, 61, 1)  # Días desde el incidente (0-60 días)
    danger_universe = arange(0, 1.01, 0.01)  # Índice de peligrosidad (0-1)

    # Variables difusas
    incidents = create_fuzzy_variable(
        "incidents",
        incidents_universe,
        {"low": (5, 2, 0), "moderate": (14, 3, 25), "high": (10, 4, 50)},
    )
    gravity = create_fuzzy_variable(
        "gravity",
        gravity_universe,
        {"low": (0.5, 3, 1), "moderate": (0.7, 3.5, 2.5), "high": (0.9, 4, 5)},
    )
    risk_zone = create_fuzzy_variable(
        "risk_zone",
        risk_zone_universe,
        {"near": (15, 2, 0), "moderate": (20, 3, 50), "far": (25, 4, 100)},
    )
    time = create_fuzzy_variable(
        "time",
        time_universe,
        {"recent": (10, 2, 0), "medium": (15, 3, 30), "old": (20, 4, 60)},
    )
    danger = create_fuzzy_variable(
        "danger",
        danger_universe,
        {
            "safe": (0.1, 2, 0),
            "low": (0.15, 3, 0.3),
            "moderate": (0.2, 3.5, 0.55),
            "high": (0.25, 4, 0.75),
            "very_high": (0.3, 4.5, 1),
        },
        is_consequent=True,
    )

    # Reglas difusas
    categories = {
        "incidents": ("low", "moderate", "high"),
        "gravity": ("low", "moderate", "high"),
        "risk_zone": ("near", "moderate", "far"),
        "time": ("recent", "medium", "old"),
    }
    consequent_map = {
        ("low", "low", "far", "old"): "safe",
        ("low", "low", "far", "medium"): "safe",
        ("low", "low", "far", "recent"): "low",
        ("low", "low", "moderate", "old"): "low",
        ("low", "low", "moderate", "medium"): "low",
        ("low", "low", "moderate", "recent"): "moderate",
        ("low", "low", "near", "old"): "low",
        ("low", "low", "near", "medium"): "moderate",
        ("low", "low", "near", "recent"): "moderate",
        ("low", "moderate", "far", "old"): "low",
        ("low", "moderate", "far", "medium"): "low",
        ("low", "moderate", "far", "recent"): "moderate",
        ("low", "moderate", "moderate", "old"): "moderate",
        ("low", "moderate", "moderate", "medium"): "moderate",
        ("low", "moderate", "moderate", "recent"): "high",
        ("low", "moderate", "near", "old"): "moderate",
        ("low", "moderate", "near", "medium"): "high",
        ("low", "moderate", "near", "recent"): "high",
        ("low", "high", "far", "old"): "moderate",
        ("low", "high", "far", "medium"): "moderate",
        ("low", "high", "far", "recent"): "high",
        ("low", "high", "moderate", "old"): "high",
        ("low", "high", "moderate", "medium"): "high",
        ("low", "high", "moderate", "recent"): "very_high",
        ("low", "high", "near", "old"): "high",
        ("low", "high", "near", "medium"): "very_high",
        ("low", "high", "near", "recent"): "very_high",
        ("moderate", "low", "far", "old"): "low",
        ("moderate", "low", "far", "medium"): "low",
        ("moderate", "low", "far", "recent"): "moderate",
        ("moderate", "low", "moderate", "old"): "moderate",
        ("moderate", "low", "moderate", "medium"): "moderate",
        ("moderate", "low", "moderate", "recent"): "high",
        ("moderate", "low", "near", "old"): "moderate",
        ("moderate", "low", "near", "medium"): "high",
        ("moderate", "low", "near", "recent"): "high",
        ("moderate", "moderate", "far", "old"): "moderate",
        ("moderate", "moderate", "far", "medium"): "moderate",
        ("moderate", "moderate", "far", "recent"): "high",
        ("moderate", "moderate", "moderate", "old"): "high",
        ("moderate", "moderate", "moderate", "medium"): "high",
        ("moderate", "moderate", "moderate", "recent"): "very_high",
        ("moderate", "moderate", "near", "old"): "high",
        ("moderate", "moderate", "near", "medium"): "very_high",
        ("moderate", "moderate", "near", "recent"): "very_high",
        ("moderate", "high", "far", "old"): "high",
        ("moderate", "high", "far", "medium"): "high",
        ("moderate", "high", "far", "recent"): "very_high",
        ("moderate", "high", "moderate", "old"): "very_high",
        ("moderate", "high", "moderate", "medium"): "very_high",
        ("moderate", "high", "moderate", "recent"): "very_high",
        ("moderate", "high", "near", "old"): "very_high",
        ("moderate", "high", "near", "medium"): "very_high",
        ("moderate", "high", "near", "recent"): "very_high",
        ("high", "low", "far", "old"): "moderate",
        ("high", "low", "far", "medium"): "moderate",
        ("high", "low", "far", "recent"): "high",
        ("high", "low", "moderate", "old"): "high",
        ("high", "low", "moderate", "medium"): "high",
        ("high", "low", "moderate", "recent"): "very_high",
        ("high", "low", "near", "old"): "high",
        ("high", "low", "near", "medium"): "very_high",
        ("high", "low", "near", "recent"): "very_high",
        ("high", "moderate", "far", "old"): "high",
        ("high", "moderate", "far", "medium"): "high",
        ("high", "moderate", "far", "recent"): "very_high",
        ("high", "moderate", "moderate", "old"): "very_high",
        ("high", "moderate", "moderate", "medium"): "very_high",
        ("high", "moderate", "moderate", "recent"): "very_high",
        ("high", "moderate", "near", "old"): "very_high",
        ("high", "moderate", "near", "medium"): "very_high",
        ("high", "moderate", "near", "recent"): "very_high",
        ("high", "high", "far", "old"): "very_high",
        ("high", "high", "far", "medium"): "very_high",
        ("high", "high", "far", "recent"): "very_high",
        ("high", "high", "moderate", "old"): "very_high",
        ("high", "high", "moderate", "medium"): "very_high",
        ("high", "high", "moderate", "recent"): "very_high",
        ("high", "high", "near", "old"): "very_high",
        ("high", "high", "near", "medium"): "very_high",
        ("high", "high", "near", "recent"): "very_high",
    }

    rules = (
        ctrl.Rule(
            incidents[inc] & gravity[grav] & risk_zone[zone] & time[tim],
            danger[consequent_map.get((inc, grav, zone, tim), "low")],
        )
        for inc, grav, zone, tim in product(*categories.values())
    )

    # Sistema difuso
    return ctrl.ControlSystem(rules)


fuzzy_system = build_fuzzy_system()


def calculate_fuzzy_danger(
    num_incidents: int,
    avg_gravity: float,
    risk_zone_distance: float,
    time: float,
) -> float:
    """
    Evalúa el nivel de peligro de una ruta usando lógica difusa.

    Args:
        num_incidents: Número de incidentes cercanos.
        avg_gravity: Gravedad promedio de los incidentes.
        risk_zone_distance: Distancia a la zona de riesgo en metros.
        time: Días que han pasado desde el incidente.

    Returns:
        Índice difuso de peligrosidad entre 0 y 1.
    """
    if num_incidents <= 0 and avg_gravity <= 0:
        return 0.0

    simulator = ctrl.ControlSystemSimulation(
        fuzzy_system,
        clip_to_bounds=True,
        cache=True,
        flush_after_run=1000,
    )

    # Definición de entradas
    simulator.inputs(
        {
            "incidents": max(0, num_incidents),
            "gravity": max(1, min(avg_gravity, 5)),
            "risk_zone": max(0, min(risk_zone_distance, 100)),
            "time": max(0, min(time, 60)),
        }
    )

    # Cálculo de salida
    simulator.compute()
    danger = round(simulator.output["danger"], 2)

    return danger
