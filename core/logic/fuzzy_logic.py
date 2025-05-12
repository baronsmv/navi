import logging

import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl

logger = logging.getLogger(__name__)


def create_fuzzy_variable(
    name: str, universe: np.ndarray, membership: dict, is_consequent: bool = False
) -> ctrl.Antecedent:
    """
    Crea una variable difusa con funciones de pertenencia.

    Args:
        name (str): Nombre de la variable.
        universe (np.ndarray): Rango de valores posibles (universo de discurso).
        membership (dict): Diccionario con funciones de pertenencia.
        is_consequent (bool): Es consecuente o, en su defecto, antecedente.

    Returns:
        ctrl.Antecedent: Variable difusa configurada.
    """
    variable = (
        ctrl.Consequent(universe, name)
        if is_consequent
        else ctrl.Antecedent(universe, name)
    )

    # Aplicación de funciones de membresía
    for label, values in membership.items():
        variable[label] = fuzz.trimf(variable.universe, values)

    return variable


def build_fuzzy_system() -> ctrl.ControlSystem:
    """
    Crea el sistema difuso para evaluar la peligrosidad de una ruta.

    Returns:
        ctrl.ControlSystem: Sistema difuso.
    """
    # Universos de valores
    incidents_universe = np.arange(0, 51, 1)  # Número de incidentes cercanos
    gravity_universe = np.arange(1, 5.1, 0.1)  # Gravedad de los incidentes (1-5)
    danger_universe = np.arange(0, 1.01, 0.01)  # Índice de peligrosidad (0-1)

    # Variables difusas
    incidents = create_fuzzy_variable(
        "incidents",
        incidents_universe,
        {"low": [0, 5, 15], "moderate": [10, 20, 30], "high": [25, 35, 50]},
    )
    gravity = create_fuzzy_variable(
        "gravity",
        gravity_universe,
        {"low": [1, 1.5, 2], "moderate": [2.5, 3, 3.5], "high": [4, 4.5, 5]},
    )
    danger = create_fuzzy_variable(
        "danger",
        danger_universe,
        {
            "safe": [0, 0.1, 0.3],
            "low_risk": [0.2, 0.4, 0.5],
            "moderate_risk": [0.4, 0.6, 0.7],
            "high_risk": [0.7, 0.9, 1],
        },
        is_consequent=True,
    )

    # Reglas difusas
    rules = [
        ctrl.Rule(incidents["low"] & gravity["low"], danger["safe"]),
        ctrl.Rule(incidents["low"] & gravity["moderate"], danger["low_risk"]),
        ctrl.Rule(incidents["low"] & gravity["high"], danger["moderate_risk"]),
        ctrl.Rule(incidents["moderate"] & gravity["low"], danger["low_risk"]),
        ctrl.Rule(incidents["moderate"] & gravity["moderate"], danger["moderate_risk"]),
        ctrl.Rule(incidents["moderate"] & gravity["high"], danger["high_risk"]),
        ctrl.Rule(incidents["high"] & gravity["low"], danger["moderate_risk"]),
        ctrl.Rule(incidents["high"] & gravity["moderate"], danger["high_risk"]),
        ctrl.Rule(incidents["high"] & gravity["high"], danger["high_risk"]),
    ]

    # Sistema difuso
    return ctrl.ControlSystem(rules)


fuzzy_system = build_fuzzy_system()


def calculate_fuzzy_danger(num_incidents: int, avg_gravity: float) -> float:
    """
    Evalúa el nivel de peligro de una ruta usando lógica difusa.

    Args:
        num_incidents (int): Número de incidentes cercanos.
        avg_gravity (float): Gravedad promedio de los incidentes.

    Returns:
        float: Índice difuso de peligrosidad entre 0 y 1.
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
        }
    )

    # Cálculo de salida
    simulator.compute()

    return round(simulator.output["danger"], 2)
