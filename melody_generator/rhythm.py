"""
Generación de patrones rítmicos.
Implementa ritmo anclado a pulsos según la jerarquía métrica.
"""

import random
from typing import List, Tuple, Optional

from .models import RhythmicPattern


class RhythmGenerator:
    """
    Genera patrones rítmicos respetando la jerarquía métrica.
    """

    def __init__(
        self,
        meter_tuple: Tuple[int, int],
        subdivisions: List[int],
        rhythmic_complexity: int,
        num_measures: int,
    ):
        """
        Inicializa el generador de ritmo.

        Args:
            meter_tuple: Compás (numerador, denominador)
            subdivisions: Subdivisiones para métricas amalgama
            rhythmic_complexity: Nivel de complejidad (1-5)
            num_measures: Número total de compases
        """
        self.meter_tuple = meter_tuple
        self.subdivisions = subdivisions
        self.rhythmic_complexity = rhythmic_complexity
        self.num_measures = num_measures
        self.strong_beats = self._calculate_strong_beats()
        self.base_rhythmic_motif: Optional[RhythmicPattern] = None

    def _calculate_strong_beats(self) -> List[int]:
        """Calcula los pulsos fuertes según la subdivisión de la métrica."""
        strong = [0]
        accumulated = 0
        for subdivision in self.subdivisions[:-1]:
            accumulated += subdivision
            strong.append(accumulated)
        return strong

    def create_rhythmic_pattern(self, num_beats: int) -> RhythmicPattern:
        """
        Crea un patrón rítmico que respeta la jerarquía métrica.

        Args:
            num_beats: Número de pulsos del patrón
        """
        durations = []

        for beat_index in range(num_beats):
            is_strong_beat = beat_index in self.strong_beats
            sixteenths_per_beat = 16 // self.meter_tuple[1]
            beat_durations = self._create_beat_subdivision(
                sixteenths_per_beat, is_strong_beat, beat_index
            )
            durations.extend(beat_durations)

        return RhythmicPattern(
            durations=durations, strong_beat_indices=self.strong_beats
        )

    def _create_beat_subdivision(
        self, sixteenths: int, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """Subdivide un pulso en duraciones que no crucen fronteras."""
        if sixteenths == 4:
            return self._subdivide_quarter_note_beat(is_strong, beat_index)
        elif sixteenths == 2:
            return self._subdivide_eighth_note_beat(is_strong, beat_index)
        elif sixteenths == 6:
            return self._subdivide_dotted_quarter_beat(is_strong, beat_index)
        else:
            return [(1, 4)]

    def _subdivide_quarter_note_beat(
        self, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """Subdivide un pulso de negra (4 sixteenths)."""
        if self.rhythmic_complexity == 1:
            if is_strong or random.random() < 0.7:
                return [(1, 4)]
            else:
                return [(1, 8), (1, 8)]

        elif self.rhythmic_complexity == 2:
            if is_strong:
                return [(1, 4)] if random.random() < 0.8 else [(1, 8), (1, 8)]
            else:
                choice = random.random()
                if choice < 0.4:
                    return [(1, 4)]
                elif choice < 0.8:
                    return [(1, 8), (1, 8)]
                else:
                    return [(3, 16), (1, 16)]

        else:  # Complejo
            if is_strong:
                return [(1, 4)] if random.random() < 0.7 else [(1, 8), (1, 8)]
            else:
                choice = random.random()
                if choice < 0.3:
                    return [(1, 4)]
                elif choice < 0.5:
                    return [(1, 8), (1, 8)]
                elif choice < 0.7:
                    return [(3, 16), (1, 16)]
                else:
                    return [(1, 16), (1, 16), (1, 16), (1, 16)]

    def _subdivide_eighth_note_beat(
        self, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """Subdivide un pulso de corchea (2 sixteenths)."""
        if is_strong or self.rhythmic_complexity <= 2:
            return [(1, 8)]
        else:
            return [(1, 8)] if random.random() < 0.7 else [(1, 16), (1, 16)]

    def _subdivide_dotted_quarter_beat(
        self, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """Subdivide un pulso de negra con puntillo (6 sixteenths)."""
        if self.rhythmic_complexity == 1:
            if is_strong or random.random() < 0.7:
                return [(3, 8)]
            else:
                return [(1, 8), (1, 8), (1, 8)]

        elif self.rhythmic_complexity == 2:
            if is_strong:
                return [(3, 8)] if random.random() < 0.8 else [(1, 8), (1, 8), (1, 8)]
            else:
                choice = random.random()
                if choice < 0.4:
                    return [(3, 8)]
                elif choice < 0.7:
                    return [(1, 8), (1, 8), (1, 8)]
                else:
                    return [(1, 8), (1, 4)]

        else:  # Complejo
            if is_strong:
                return [(3, 8)] if random.random() < 0.7 else [(1, 8), (1, 8), (1, 8)]
            else:
                choice = random.random()
                if choice < 0.25:
                    return [(3, 8)]
                elif choice < 0.5:
                    return [(1, 8), (1, 8), (1, 8)]
                elif choice < 0.75:
                    return [(1, 8), (1, 4)]
                else:
                    return [(1, 16)] * 6

    def get_rhythmic_pattern_with_variation(
        self, measure_index: int
    ) -> RhythmicPattern:
        """
        Obtiene el patrón rítmico para un compás, aplicando variaciones al motivo base.

        Args:
            measure_index: Índice del compás (0 = primer compás)

        Returns:
            RhythmicPattern basado en el motivo original con posibles variaciones
        """
        if self.base_rhythmic_motif is None:
            return self.create_rhythmic_pattern(self.meter_tuple[0])

        # Primer compás: usar motivo original
        if measure_index == 0:
            return self.base_rhythmic_motif

        # Segundo compás: repetir motivo exacto
        if measure_index == 1:
            return self.base_rhythmic_motif

        # Cadencias: usar motivo original
        midpoint = self.num_measures // 2
        is_antecedent_end = measure_index == midpoint - 1
        is_period_end = measure_index == self.num_measures - 1

        if is_antecedent_end or is_period_end:
            return self.base_rhythmic_motif

        # Otros compases: aplicar variaciones sutiles
        if random.random() < 0.3:
            return self._apply_rhythmic_variation(self.base_rhythmic_motif)
        else:
            return self.base_rhythmic_motif

    def _apply_rhythmic_variation(self, motif: RhythmicPattern) -> RhythmicPattern:
        """Aplica una variación sutil al motivo rítmico."""
        variation_type = random.choice(["retrograde", "original", "original"])

        if variation_type == "retrograde":
            reversed_durations = list(reversed(motif.durations))
            return RhythmicPattern(
                durations=reversed_durations,
                strong_beat_indices=motif.strong_beat_indices,
            )
        else:
            return motif

    def initialize_base_motif(self):
        """Inicializa el motivo rítmico base para cohesión melódica."""
        self.base_rhythmic_motif = self.create_rhythmic_pattern(self.meter_tuple[0])
