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
            # Modo menor: usar V mayor para cadencias fuertes (práctica común)
            # En la teoría clásica, V siempre se altera a mayor para cadencias
            self.chord_qualities = {
                1: "minor",
                2: "diminished",
                3: "major",
                4: "minor",      # iv natural, pero IV mayor disponible en cadencias
                5: "major",      # V mayor (práctica común, incluso en menor natural)
                6: "major",
                7: "diminished", # vii° (sensible) para conducción a tónica
            }
            # Menor armónica ya tiene V mayor y vii° naturalmente
            if self.mode == "harmonic_minor":
                pass  # Ya configurado correctamente arriba

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

        Sigue la estructura clásica:
        - Antecedente: termina en V (semicadencia)
        - Consecuente: termina en I (cadencia auténtica)
        - Períodos completos siempre terminan en I

        Args:
            num_measures: Número de compases del período

        Returns:
            Lista de HarmonicFunction, una por compás
        """
        progression = []

        # Generar progresión según longitud
        if num_measures == 1:
            degrees = [1]
        elif num_measures == 2:
            # Período mínimo: I → I (reposo)
            degrees = [1, 1]
        elif num_measures == 3:
            # I → IV → I (subdominante como tensión intermedia)
            degrees = [1, 4, 1]
        elif num_measures == 4:
            # Antecedente corto: I → I → IV → I
            # (No hay semicadencia porque no hay consecuente)
            degrees = [1, 1, 4, 1]
        elif num_measures <= 8:
            # Período clásico: antecedente (termina V) + consecuente (termina I)
            midpoint = num_measures // 2
            # Antecedente: I...V
            antecedent = [1] * (midpoint - 1) + [5]
            if midpoint >= 3:
                antecedent[-2] = 4  # Subdominante antes de dominante
            # Consecuente: I...I
            consequent_len = num_measures - midpoint
            consequent = [1] * (consequent_len - 1) + [1]
            if consequent_len >= 3:
                consequent[-2] = 5  # V → I para cadencia auténtica
            if consequent_len >= 4:
                consequent[-3] = 4  # IV → V → I
            degrees = antecedent + consequent
        else:
            # Períodos largos: múltiples frases de 4 compases
            num_phrases = (num_measures + 3) // 4
            degrees = []
            for phrase_idx in range(num_phrases):
                remaining = num_measures - len(degrees)
                if remaining <= 0:
                    break

                is_last_phrase = phrase_idx == num_phrases - 1
                phrase_len = min(4, remaining)

                if is_last_phrase:
                    # Última frase: termina en I (cadencia auténtica)
                    if phrase_len == 4:
                        phrase = [1, 1, 5, 1]  # I → I → V → I
                    elif phrase_len == 3:
                        phrase = [1, 5, 1]
                    elif phrase_len == 2:
                        phrase = [5, 1]
                    else:
                        phrase = [1]
                elif phrase_idx == num_phrases // 2 - 1:
                    # Mitad del período: semicadencia (termina en V)
                    if phrase_len == 4:
                        phrase = [1, 1, 4, 5]
                    elif phrase_len == 3:
                        phrase = [1, 4, 5]
                    else:
                        phrase = [1, 5][:phrase_len]
                else:
                    # Frases intermedias: progresión normal
                    if phrase_len == 4:
                        phrase = [1, 1, 4, 1]
                    elif phrase_len == 3:
                        phrase = [1, 4, 1]
                    else:
                        phrase = [1] * phrase_len

                degrees.extend(phrase)

            degrees = degrees[:num_measures]

        # GARANTÍA: El período siempre termina en I (tónica)
        if degrees:
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
