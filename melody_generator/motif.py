"""
Creación y variación de motivos melódicos.
Implementa técnicas de desarrollo temático según teoría musical clásica.
"""

import random
from typing import List, Tuple, Optional

from music21 import pitch

from .models import Motif, RhythmicPattern, MotivicVariation, MelodicContour
from .scales import ScaleManager
from .harmony import HarmonyManager


class MotifGenerator:
    """
    Genera y varía motivos melódicos según las reglas de la teoría musical.
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        harmony_manager: HarmonyManager,
        rhythmic_complexity: int,
        variation_freedom: int = 2,
        use_motivic_variations: bool = True,
        variation_probability: float = 0.4,
        contour: Optional[MelodicContour] = None,
        climax_measure: int = 6,
    ):
        """
        Inicializa el generador de motivos.

        Args:
            scale_manager: Gestor de escalas
            harmony_manager: Gestor de armonía
            rhythmic_complexity: Nivel de complejidad rítmica (1-5)
            variation_freedom: Libertad de variación (1=estricta, 2=moderada, 3=libre)
            use_motivic_variations: Si se deben aplicar variaciones
            variation_probability: Probabilidad de aplicar variación
            contour: Configuración del contorno melódico
            climax_measure: Compás donde ocurre el clímax
        """
        self.scale_manager = scale_manager
        self.harmony_manager = harmony_manager
        self.rhythmic_complexity = rhythmic_complexity
        self.variation_freedom = variation_freedom
        self.use_motivic_variations = use_motivic_variations
        self.variation_probability = variation_probability
        self.contour = contour or MelodicContour()
        self.climax_measure = climax_measure
        self.original_motif: Optional[Motif] = None

    def create_base_motif(self, harmonic_function: int = 1) -> Motif:
        """
        Genera el motivo base (célula melódica de 2-4 notas).

        Args:
            harmonic_function: Grado del acorde base (1=I, 4=IV, 5=V)

        Returns:
            Motif con pitches, intervalos, ritmo y grados
        """
        motif_length_beats = random.choice([1, 2])

        # Crear patrón rítmico
        if motif_length_beats == 1:
            if self.rhythmic_complexity <= 2:
                durations = [(1, 8), (1, 8)]
            else:
                durations = random.choice(
                    [
                        [(1, 8), (1, 8), (1, 8), (1, 8)],
                        [(1, 8), (3, 16)],
                        [(3, 16), (1, 16), (1, 8)],
                    ]
                )
        else:
            if self.rhythmic_complexity <= 2:
                durations = [(1, 4), (1, 4)]
            else:
                durations = random.choice(
                    [
                        [(1, 4), (1, 8), (1, 8)],
                        [(3, 8), (1, 8)],
                        [(1, 8), (1, 8), (1, 4)],
                    ]
                )

        rhythm = RhythmicPattern(durations=durations, strong_beat_indices=[0])

        # Generar grados melódicos
        chord_tones = self.harmony_manager.get_chord_tones_for_function(
            harmonic_function
        )
        contour_type = random.choice(
            ["ascending", "descending", "arch", "inverted_arch"]
        )

        num_notes = len(durations)
        degrees = []
        pitches = []
        intervals = []

        # Primera nota
        if random.random() < 0.6:
            first_degree = 1 if harmonic_function == 1 else harmonic_function
        else:
            first_degree = random.choice(chord_tones)

        degrees.append(first_degree)
        first_pitch_str = self.scale_manager.get_pitch_by_degree(first_degree)
        pitches.append(first_pitch_str)

        # Generar notas restantes según el contorno
        for i in range(1, num_notes):
            if contour_type == "ascending":
                interval_semitones = random.choice([1, 2, 3, 4])
            elif contour_type == "descending":
                interval_semitones = random.choice([-1, -2, -3, -4])
            elif contour_type == "arch":
                if i <= num_notes // 2:
                    interval_semitones = random.choice([1, 2, 3])
                else:
                    interval_semitones = random.choice([-1, -2, -3])
            else:
                if i <= num_notes // 2:
                    interval_semitones = random.choice([-1, -2, -3])
                else:
                    interval_semitones = random.choice([1, 2, 3])

            prev_pitch = pitch.Pitch(pitches[-1])
            new_pitch = prev_pitch.transpose(interval_semitones)

            # Verificar ámbito
            if new_pitch.ps < self.scale_manager.melodic_range_bottom.ps:
                new_pitch = self.scale_manager.melodic_range_bottom.transpose(
                    random.choice([0, 2, 4])
                )
            elif new_pitch.ps > self.scale_manager.melodic_range_top.ps:
                new_pitch = self.scale_manager.melodic_range_top.transpose(
                    random.choice([0, -2, -4])
                )

            pitches.append(new_pitch.nameWithOctave)
            intervals.append(interval_semitones)
            degree = self.scale_manager.pitch_to_degree(new_pitch.nameWithOctave)
            degrees.append(degree)

        return Motif(
            pitches=pitches, intervals=intervals, rhythm=rhythm, degrees=degrees
        )

    def apply_motivic_variation_to_degrees(
        self, degrees: List[int], variation_type: MotivicVariation
    ) -> List[int]:
        """Aplica una variación motívica a una secuencia de grados."""
        if variation_type == MotivicVariation.ORIGINAL:
            return degrees

        elif variation_type == MotivicVariation.INVERSION:
            if len(degrees) < 2:
                return degrees
            result = [degrees[0]]
            for i in range(1, len(degrees)):
                interval_original = degrees[i] - degrees[i - 1]
                new_degree = result[-1] - interval_original
                while new_degree < 1:
                    new_degree += 7
                while new_degree > 7:
                    new_degree -= 7
                result.append(new_degree)
            return result

        elif variation_type == MotivicVariation.RETROGRADE:
            return list(reversed(degrees))

        elif variation_type == MotivicVariation.RETROGRADE_INVERSION:
            reversed_degrees = list(reversed(degrees))
            return self.apply_motivic_variation_to_degrees(
                reversed_degrees, MotivicVariation.INVERSION
            )

        elif variation_type == MotivicVariation.TRANSPOSITION:
            transpose_interval = random.choice([2, 3, 4, 5])
            result = []
            for deg in degrees:
                new_deg = deg + transpose_interval
                while new_deg > 7:
                    new_deg -= 7
                result.append(new_deg)
            return result

        elif variation_type == MotivicVariation.SEQUENCE:
            return self.apply_motivic_variation_to_degrees(
                degrees, MotivicVariation.TRANSPOSITION
            )

        return degrees

    def apply_rhythmic_variation(
        self, durations: List[Tuple[int, int]], variation_type: MotivicVariation
    ) -> List[Tuple[int, int]]:
        """Aplica variación rítmica (aumentación o disminución)."""
        if variation_type == MotivicVariation.AUGMENTATION:
            return [(num * 2, denom) for num, denom in durations]
        elif variation_type == MotivicVariation.DIMINUTION:
            result = []
            for num, denom in durations:
                if num >= 2:
                    result.append((num // 2, denom))
                else:
                    result.append((num, denom * 2))
            return result
        return durations

    def select_variation_type(self, measure_index: int) -> MotivicVariation:
        """Selecciona un tipo de variación motívica según el contexto."""
        if not self.use_motivic_variations:
            return MotivicVariation.ORIGINAL

        if random.random() > self.variation_probability:
            return MotivicVariation.ORIGINAL

        distance_to_climax = abs(measure_index - self.climax_measure)

        if distance_to_climax <= 1:
            return random.choice(
                [
                    MotivicVariation.INVERSION,
                    MotivicVariation.AUGMENTATION,
                    MotivicVariation.SEQUENCE,
                ]
            )
        elif measure_index < self.climax_measure:
            return random.choice(
                [
                    MotivicVariation.TRANSPOSITION,
                    MotivicVariation.SEQUENCE,
                    MotivicVariation.ORIGINAL,
                ]
            )
        else:
            return random.choice(
                [
                    MotivicVariation.RETROGRADE,
                    MotivicVariation.DIMINUTION,
                    MotivicVariation.ORIGINAL,
                ]
            )

    def apply_motif_variation(
        self, original_motif: Motif, variation_type: str = "auto"
    ) -> Motif:
        """
        Aplica una variación a un motivo según el nivel de libertad configurado.

        Args:
            original_motif: Motivo original a variar
            variation_type: "auto", "strict", "moderate", o "free"

        Returns:
            Nuevo Motif con la variación aplicada
        """
        if variation_type == "auto":
            freedom = self.variation_freedom
        elif variation_type == "strict":
            freedom = 1
        elif variation_type == "moderate":
            freedom = 2
        elif variation_type == "free":
            freedom = 3
        else:
            freedom = self.variation_freedom

        # Seleccionar tipo de variación según libertad
        if freedom == 1:
            variation_options = [
                MotivicVariation.ORIGINAL,
                MotivicVariation.RETROGRADE,
                MotivicVariation.TRANSPOSITION,
            ]
            weights = [0.4, 0.3, 0.3]
        elif freedom == 2:
            variation_options = [
                MotivicVariation.ORIGINAL,
                MotivicVariation.RETROGRADE,
                MotivicVariation.INVERSION,
                MotivicVariation.TRANSPOSITION,
                MotivicVariation.AUGMENTATION,
                MotivicVariation.DIMINUTION,
            ]
            weights = [0.2, 0.2, 0.2, 0.2, 0.1, 0.1]
        else:
            variation_options = list(MotivicVariation)
            weights = [1 / len(variation_options)] * len(variation_options)

        variation = random.choices(variation_options, weights=weights)[0]

        return self._apply_variation(original_motif, variation)

    def _apply_variation(
        self, original_motif: Motif, variation: MotivicVariation
    ) -> Motif:
        """Aplica una variación específica a un motivo."""
        if variation == MotivicVariation.ORIGINAL:
            return original_motif

        elif variation == MotivicVariation.RETROGRADE:
            return Motif(
                pitches=list(reversed(original_motif.pitches)),
                intervals=list(reversed([-i for i in original_motif.intervals])),
                rhythm=RhythmicPattern(
                    durations=list(reversed(original_motif.rhythm.durations)),
                    strong_beat_indices=original_motif.rhythm.strong_beat_indices,
                ),
                degrees=list(reversed(original_motif.degrees)),
            )

        elif variation == MotivicVariation.INVERSION:
            new_pitches = [original_motif.pitches[0]]
            new_degrees = [original_motif.degrees[0]]
            new_intervals = []

            for interval_semi in original_motif.intervals:
                inverted_interval = -interval_semi
                new_intervals.append(inverted_interval)

                prev_pitch = pitch.Pitch(new_pitches[-1])
                new_pitch = prev_pitch.transpose(inverted_interval)

                if new_pitch.ps < self.scale_manager.melodic_range_bottom.ps:
                    new_pitch = self.scale_manager.melodic_range_bottom.transpose(
                        random.choice([0, 2, 4])
                    )
                elif new_pitch.ps > self.scale_manager.melodic_range_top.ps:
                    new_pitch = self.scale_manager.melodic_range_top.transpose(
                        random.choice([0, -2, -4])
                    )

                new_pitches.append(new_pitch.nameWithOctave)
                new_degrees.append(
                    self.scale_manager.pitch_to_degree(new_pitch.nameWithOctave)
                )

            return Motif(
                pitches=new_pitches,
                intervals=new_intervals,
                rhythm=original_motif.rhythm,
                degrees=new_degrees,
            )

        elif variation == MotivicVariation.TRANSPOSITION:
            transposition_steps = random.choice([-2, -1, 1, 2])
            new_pitches = []
            new_degrees = []

            for p_str in original_motif.pitches:
                p = pitch.Pitch(p_str)
                new_p = p.transpose(transposition_steps)

                if new_p.ps < self.scale_manager.melodic_range_bottom.ps:
                    new_p = new_p.transpose(12)
                elif new_p.ps > self.scale_manager.melodic_range_top.ps:
                    new_p = new_p.transpose(-12)

                new_pitches.append(new_p.nameWithOctave)
                new_degrees.append(
                    self.scale_manager.pitch_to_degree(new_p.nameWithOctave)
                )

            return Motif(
                pitches=new_pitches,
                intervals=original_motif.intervals,
                rhythm=original_motif.rhythm,
                degrees=new_degrees,
            )

        elif variation == MotivicVariation.AUGMENTATION:
            augmented_durations = []
            for num, denom in original_motif.rhythm.durations:
                new_denom = max(1, denom // 2)
                augmented_durations.append((num, new_denom))

            return Motif(
                pitches=original_motif.pitches,
                intervals=original_motif.intervals,
                rhythm=RhythmicPattern(
                    durations=augmented_durations,
                    strong_beat_indices=original_motif.rhythm.strong_beat_indices,
                ),
                degrees=original_motif.degrees,
            )

        elif variation == MotivicVariation.DIMINUTION:
            diminished_durations = []
            for num, denom in original_motif.rhythm.durations:
                new_denom = min(32, denom * 2)
                diminished_durations.append((num, new_denom))

            return Motif(
                pitches=original_motif.pitches,
                intervals=original_motif.intervals,
                rhythm=RhythmicPattern(
                    durations=diminished_durations,
                    strong_beat_indices=original_motif.rhythm.strong_beat_indices,
                ),
                degrees=original_motif.degrees,
            )

        else:
            return original_motif
