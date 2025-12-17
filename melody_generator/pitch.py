"""
Selección de tonos y control del contorno melódico.
Implementa reglas teóricas de movimiento melódico.
"""

import random
from typing import Tuple, Optional, List

from music21 import pitch, interval

from .models import (
    NoteFunction,
    RhythmicPattern,
    MelodicContour,
    ImpulseType,
)
from .scales import ScaleManager
from .harmony import HarmonyManager


class PitchSelector:
    """
    Selecciona tonos melódicos según las reglas de la teoría musical.
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        harmony_manager: HarmonyManager,
        contour: MelodicContour,
        num_measures: int,
        max_interval: int = 6,
        use_tenoris: bool = False,
        tenoris_probability: float = 0.2,
        infraction_rate: float = 0.1,
        use_rests: bool = True,
        rest_probability: float = 0.15,
        impulse_type: ImpulseType = ImpulseType.TETIC,
        meter_tuple: Tuple[int, int] = (4, 4),
    ):
        """
        Inicializa el selector de tonos.
        """
        self.scale_manager = scale_manager
        self.harmony_manager = harmony_manager
        self.contour = contour
        self.num_measures = num_measures
        self.max_interval = max_interval
        self.use_tenoris = use_tenoris
        self.tenoris_probability = tenoris_probability
        self.infraction_rate = infraction_rate
        self.use_rests = use_rests
        self.rest_probability = rest_probability
        self.impulse_type = impulse_type
        self.meter_tuple = meter_tuple

        # Estado interno
        self.current_octave = 4
        self.last_pitch: Optional[str] = None
        self.last_interval_direction: Optional[int] = None
        self.infraction_pending_compensation = False
        self.last_was_rest = False
        self.must_recover_leap = False

        # Control del clímax
        self.climax_measure = int(num_measures * contour.climax_position)
        self.climax_reached = False
        self.current_highest_pitch: Optional[str] = None

    def calculate_climax_influence(self, measure_index: int) -> float:
        """Calcula el factor de influencia del clímax en el registro actual."""
        distance_to_climax = abs(measure_index - self.climax_measure)
        approach_range = self.contour.climax_approach_range

        if measure_index == self.climax_measure:
            return self.contour.climax_emphasis
        elif distance_to_climax <= approach_range:
            proximity = 1.0 - (distance_to_climax / approach_range)
            return 1.0 + (self.contour.climax_emphasis - 1.0) * proximity
        else:
            return 1.0

    def select_melodic_pitch(
        self,
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        rhythm_pattern: RhythmicPattern,
        note_index_in_measure: int,
    ) -> Tuple[str, NoteFunction]:
        """
        Selecciona el tono melódico según las reglas de la teoría musical.

        Returns:
            Tupla de (nota, función)
        """
        harmonic_function = self.harmony_manager.get_harmonic_function(
            measure_index, beat_index
        )
        chord_tones = self.harmony_manager.get_chord_tones_for_function(
            harmonic_function
        )

        should_be_structural = is_strong_beat

        # Sistema de infracción
        if (
            random.random() < self.infraction_rate
            and not self.infraction_pending_compensation
        ):
            should_be_structural = not should_be_structural
            self.infraction_pending_compensation = True
        elif self.infraction_pending_compensation:
            should_be_structural = True
            self.infraction_pending_compensation = False

        # Considerar tenoris
        use_tenoris_now = (
            self.use_tenoris
            and should_be_structural
            and random.random() < self.tenoris_probability
            and not is_strong_beat
        )

        if use_tenoris_now:
            degree = 5
            function = NoteFunction.STRUCTURAL
        elif should_be_structural:
            degree = random.choice(chord_tones)
            function = NoteFunction.STRUCTURAL
        else:
            if self.last_pitch:
                last_degree = self.scale_manager.pitch_to_degree(self.last_pitch)
                if random.random() < 0.5:
                    degree = last_degree + 1 if last_degree < 7 else 1
                else:
                    degree = last_degree - 1 if last_degree > 1 else 7
                function = NoteFunction.PASSING
            else:
                degree = 2
                function = NoteFunction.PASSING

        note_pitch = self.scale_manager.get_pitch_by_degree(degree, self.current_octave)

        if self.last_pitch:
            note_pitch = self._adjust_octave_for_contour(
                note_pitch, measure_index, is_structural=should_be_structural
            )

        self.last_pitch = note_pitch
        return note_pitch, function

    def _adjust_octave_for_contour(
        self, new_pitch: str, measure_index: int = 0, is_structural: bool = True
    ) -> str:
        """Ajusta la octava para mantener un contorno melódico apropiado."""
        if not self.last_pitch:
            new_p = pitch.Pitch(new_pitch)
            for test_octave in [3, 4, 5]:
                test_p = pitch.Pitch(f"{new_p.name}{test_octave}")
                if self.scale_manager.is_in_range(test_p):
                    return f"{new_p.name}{test_octave}"
            return new_pitch

        last_p = pitch.Pitch(self.last_pitch)
        new_p = pitch.Pitch(new_pitch)

        # Si debemos recuperar un salto
        if self.must_recover_leap and self.last_interval_direction is not None:
            best_octave = new_p.octave
            best_interval = 100

            for octave_adj in [-1, 0, 1]:
                test_octave = new_p.octave + octave_adj
                test_p = pitch.Pitch(f"{new_p.name}{test_octave}")

                if not self.scale_manager.is_in_range(test_p):
                    continue

                intv = interval.Interval(last_p, test_p)
                intv_semitones = intv.semitones
                intv_size = abs(intv_semitones)

                current_direction = (
                    1 if intv_semitones > 0 else -1 if intv_semitones < 0 else 0
                )

                if (
                    current_direction != 0
                    and current_direction != self.last_interval_direction
                ):
                    if intv_size <= 2 and intv_size < best_interval:
                        best_interval = intv_size
                        best_octave = test_octave

            if best_interval < 100:
                result = f"{new_p.name}{best_octave}"
                result_p = pitch.Pitch(result)
                intv = interval.Interval(last_p, result_p)
                self.last_interval_direction = (
                    1 if intv.semitones > 0 else -1 if intv.semitones < 0 else 0
                )
                self.must_recover_leap = False
                return result

        # Búsqueda normal de octava óptima
        best_octave = new_p.octave
        best_interval_size = 100

        for octave_adj in [-1, 0, 1, 2]:
            test_octave = new_p.octave + octave_adj
            test_p = pitch.Pitch(f"{new_p.name}{test_octave}")

            if not self.scale_manager.is_in_range(test_p):
                continue

            intv = interval.Interval(last_p, test_p)
            intv_semitones = abs(intv.semitones)

            max_allowed = self.max_interval

            if is_structural and measure_index == self.climax_measure:
                max_allowed = 12
            elif intv_semitones > 9:
                continue

            if intv_semitones > max_allowed:
                continue

            score = intv_semitones
            if intv_semitones <= 2:
                score -= 10
            elif intv_semitones <= 5:
                score -= 5

            if score < best_interval_size:
                best_interval_size = score
                best_octave = test_octave

        result = f"{new_p.name}{best_octave}"
        result_p = pitch.Pitch(result)

        intv = interval.Interval(last_p, result_p)
        intv_semitones = intv.semitones
        intv_size = abs(intv_semitones)

        if intv_size > 4:
            self.must_recover_leap = True
            self.last_interval_direction = 1 if intv_semitones > 0 else -1
        else:
            self.last_interval_direction = (
                1 if intv_semitones > 0 else -1 if intv_semitones < 0 else 0
            )

        if (
            self.current_highest_pitch is None
            or result_p.ps > pitch.Pitch(self.current_highest_pitch).ps
        ):
            self.current_highest_pitch = result
            if measure_index == self.climax_measure:
                self.climax_reached = True

        return result

    def should_use_rest(
        self,
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        is_phrase_boundary: bool,
    ) -> bool:
        """Determina si se debe usar un silencio en este punto."""
        if not self.use_rests:
            return False

        if self.last_was_rest:
            return False

        is_final_measure = measure_index == self.num_measures - 1
        is_semifinal_measure = measure_index == (self.num_measures // 2) - 1
        is_last_beat = beat_index >= self.meter_tuple[0] - 1

        if (is_final_measure or is_semifinal_measure) and is_last_beat:
            return False

        if is_phrase_boundary and beat_index == self.meter_tuple[0] - 1:
            return random.random() < self.rest_probability * 2

        if (
            self.impulse_type == ImpulseType.ANACROUSTIC
            and beat_index == 0
            and measure_index % 2 == 0
        ):
            return random.random() < self.rest_probability * 1.5

        if (
            self.impulse_type == ImpulseType.ACEPHALOUS
            and is_strong_beat
            and measure_index % 3 == 0
        ):
            return random.random() < self.rest_probability * 1.2

        if not is_strong_beat:
            return random.random() < self.rest_probability * 0.5

        return False

    def set_last_was_rest(self, value: bool):
        """Actualiza el estado de si el último evento fue silencio."""
        self.last_was_rest = value
