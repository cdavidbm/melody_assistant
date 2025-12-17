"""
Gestión de armonía y progresiones armónicas.
Implementa la armonía implícita según teoría musical clásica.
"""

import random
from typing import List

from .models import HarmonicFunction


class HarmonyManager:
    """
    Gestiona las funciones armónicas y progresiones para la generación melódica.
    """

    def __init__(self, mode: str, num_measures: int, strong_beats: List[int]):
        """
        Inicializa el gestor de armonía.

        Args:
            mode: Modo musical actual
            num_measures: Número total de compases
            strong_beats: Lista de índices de tiempos fuertes
        """
        self.mode = mode
        self.num_measures = num_measures
        self.strong_beats = strong_beats
        self._setup_chord_qualities()

    def _setup_chord_qualities(self):
        """Configura las calidades de acordes según el modo."""
        if self.mode in ["major", "lydian", "mixolydian"]:
            self.chord_qualities = {
                1: "major",
                2: "minor",
                3: "minor",
                4: "major",
                5: "major",
                6: "minor",
                7: "diminished",
            }
        else:
            self.chord_qualities = {
                1: "minor",
                2: "diminished",
                3: "major",
                4: "minor",
                5: "minor",
                6: "major",
                7: "major",
            }
            if self.mode == "harmonic_minor":
                self.chord_qualities[5] = "major"
                self.chord_qualities[7] = "diminished"

        self.tension_levels = {
            1: 0.0,
            2: 0.4,
            3: 0.3,
            4: 0.5,
            5: 0.8,
            6: 0.3,
            7: 0.9,
        }

    def get_harmonic_function(self, measure_index: int, beat_index: int) -> int:
        """
        Retorna el acorde implícito para un punto específico.

        Args:
            measure_index: Índice del compás
            beat_index: Índice del pulso

        Returns:
            1 para tónica (I), 5 para dominante (V), 4 para subdominante (IV)
        """
        is_semifinal_measure = measure_index == (self.num_measures // 2) - 1
        is_final_measure = measure_index == self.num_measures - 1

        # Antecedente termina en V (semicadencia)
        if is_semifinal_measure and beat_index >= len(self.strong_beats) - 1:
            return 5

        # Consecuente termina en I (cadencia auténtica)
        if is_final_measure and beat_index >= len(self.strong_beats) - 1:
            return 1

        # Progresión armónica por medida
        if measure_index % 4 == 0:
            return 1
        elif measure_index % 4 == 1:
            return 4 if random.random() < 0.4 else 1
        elif measure_index % 4 == 2:
            return 5
        else:
            return 1

    def get_chord_tones_for_function(self, harmonic_function: int) -> List[int]:
        """
        Retorna los grados de la escala que forman el acorde.

        Args:
            harmonic_function: Grado del acorde (1, 4, 5)

        Returns:
            Lista de grados que forman el acorde
        """
        if harmonic_function == 1:
            return [1, 3, 5]
        elif harmonic_function == 4:
            return [4, 6, 1]
        elif harmonic_function == 5:
            return [5, 7, 2]
        return [1, 3, 5]

    def create_harmonic_progression(self, num_measures: int) -> List[HarmonicFunction]:
        """
        Crea una progresión armónica implícita para un período.

        Args:
            num_measures: Número de compases del período

        Returns:
            Lista de HarmonicFunction, una por compás
        """
        progression = []

        # Generar progresión según longitud
        if num_measures <= 2:
            degrees = [1, 5] if num_measures == 2 else [1]
        elif num_measures <= 4:
            degrees = [1, 1, 4, 5] if num_measures == 4 else [1, 4, 5]
        elif num_measures <= 8:
            antecedent = [1, 1, 4, 5]
            consequent = [1, 1, 4, 5] if num_measures == 8 else [1, 4, 5]
            consequent[-1] = 1
            degrees = antecedent + consequent[: num_measures - 4]
        else:
            num_periods = (num_measures + 7) // 8
            degrees = []
            for period_idx in range(num_periods):
                if period_idx < num_periods - 1:
                    degrees.extend([1, 1, 4, 5, 1, 1, 4, 5])
                else:
                    remaining = num_measures - len(degrees)
                    if remaining >= 8:
                        degrees.extend([1, 1, 4, 5, 1, 1, 4, 1])
                    elif remaining >= 4:
                        degrees.extend([1, 1, 4, 5])
                        degrees.extend([1] * (remaining - 4))
                    else:
                        degrees.extend([1] * remaining)
            degrees = degrees[:num_measures]
            degrees[-1] = 1

        # Convertir a HarmonicFunction objects
        for degree in degrees:
            quality = self.chord_qualities.get(degree, "major")
            tension = self.tension_levels.get(degree, 0.5)
            chord_tones = self.get_chord_tones_for_function(degree)
            progression.append(
                HarmonicFunction(
                    degree=degree,
                    quality=quality,
                    tension=tension,
                    chord_tones=chord_tones,
                )
            )

        return progression
