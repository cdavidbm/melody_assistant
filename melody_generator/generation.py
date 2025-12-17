"""
Métodos de generación de períodos musicales.
Implementa generación tradicional (cohesión rítmica) y jerárquica (formal).
"""

import random
from fractions import Fraction
from typing import Tuple

import abjad

from .models import Motif, HarmonicFunction
from .scales import ScaleManager
from .harmony import HarmonyManager
from .rhythm import RhythmGenerator
from .pitch import PitchSelector
from .motif import MotifGenerator
from .lilypond import LilyPondFormatter


class PeriodGenerator:
    """
    Genera períodos musicales completos usando diferentes métodos.
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        harmony_manager: HarmonyManager,
        rhythm_generator: RhythmGenerator,
        pitch_selector: PitchSelector,
        motif_generator: MotifGenerator,
        lilypond_formatter: LilyPondFormatter,
        num_measures: int,
        meter_tuple: Tuple[int, int],
    ):
        """
        Inicializa el generador de períodos.
        """
        self.scale_manager = scale_manager
        self.harmony_manager = harmony_manager
        self.rhythm_generator = rhythm_generator
        self.pitch_selector = pitch_selector
        self.motif_generator = motif_generator
        self.lilypond_formatter = lilypond_formatter
        self.num_measures = num_measures
        self.meter_tuple = meter_tuple

    def generate_period(self) -> abjad.Staff:
        """
        Genera un período musical completo (método tradicional).

        Implementa la estructura de pregunta-respuesta con cadencias apropiadas.
        Genera un motivo rítmico base que se reutiliza para cohesión.
        """
        staff = abjad.Staff(name="Melodia")

        self.rhythm_generator.initialize_base_motif()

        midpoint = self.num_measures // 2

        for m_idx in range(self.num_measures):
            is_antecedent_end = m_idx == midpoint - 1
            is_period_end = m_idx == self.num_measures - 1

            if is_period_end:
                container = self._create_measure(
                    m_idx, is_cadence=True, cadence_type="authentic"
                )
            elif is_antecedent_end:
                container = self._create_measure(
                    m_idx, is_cadence=True, cadence_type="half"
                )
            else:
                container = self._create_measure(m_idx, is_cadence=False)

            staff.append(container)

            if m_idx < self.num_measures - 1:
                last_leaf = abjad.get.leaf(container, -1)
                if last_leaf:
                    abjad.attach(abjad.BarLine("|"), last_leaf)
            else:
                last_leaf = abjad.get.leaf(container, -1)
                if last_leaf:
                    abjad.attach(abjad.BarLine("|."), last_leaf)

        self._add_staff_indications(staff)
        self._add_ties_to_staff(staff)

        return staff

    def generate_period_hierarchical(self) -> abjad.Staff:
        """
        Genera un período musical con jerarquía formal verdadera.

        Implementa la estructura:
        Motivo → Frase (2 compases) → Semifrase (4 compases) → Período (8+ compases)
        """
        staff = abjad.Staff(name="Melodia_Hierarchical")

        harmonic_progression = self.harmony_manager.create_harmonic_progression(
            self.num_measures
        )
        base_motif = self.motif_generator.create_base_motif(
            harmonic_progression[0].degree
        )

        num_phrases = (self.num_measures + 1) // 2

        for phrase_idx in range(num_phrases):
            measure_start = phrase_idx * 2
            measure_end = min(measure_start + 2, self.num_measures)

            if phrase_idx == 0:
                variation_types = ["auto", "auto"]
            elif measure_end == self.num_measures // 2:
                variation_types = ["auto", "strict"]
            elif phrase_idx == num_phrases - 1:
                variation_types = ["strict", "strict"]
            else:
                variation_types = ["auto", "auto"]

            for local_measure_idx in range(measure_end - measure_start):
                global_measure_idx = measure_start + local_measure_idx

                if global_measure_idx >= self.num_measures:
                    break

                if local_measure_idx == 0:
                    if phrase_idx == 0:
                        current_motif = base_motif
                    else:
                        current_motif = self.motif_generator.apply_motif_variation(
                            base_motif, variation_type=variation_types[0]
                        )
                else:
                    current_motif = self.motif_generator.apply_motif_variation(
                        base_motif, variation_type=variation_types[1]
                    )

                harmonic_func = harmonic_progression[global_measure_idx]
                measure_container = self._create_measure_from_motif(
                    current_motif, harmonic_func, global_measure_idx
                )

                staff.append(measure_container)

                if global_measure_idx < self.num_measures - 1:
                    last_leaf = abjad.get.leaf(measure_container, -1)
                    if last_leaf:
                        abjad.attach(abjad.BarLine("|"), last_leaf)
                else:
                    last_leaf = abjad.get.leaf(measure_container, -1)
                    if last_leaf:
                        abjad.attach(abjad.BarLine("|."), last_leaf)

        self._add_staff_indications(staff)

        return staff

    def _create_measure(
        self,
        measure_index: int,
        is_cadence: bool = False,
        cadence_type: str = "authentic",
    ) -> abjad.Container:
        """Crea un compás basado en la estructura de pulsos y la teoría armónica."""
        notes = []

        rhythm_pattern = self.rhythm_generator.get_rhythmic_pattern_with_variation(
            measure_index
        )

        current_position = Fraction(0)
        total_ql = Fraction(self.meter_tuple[0], self.meter_tuple[1]) * 4

        for note_index, duration in enumerate(rhythm_pattern.durations):
            duration_ql = Fraction(duration[0], duration[1]) * 4
            beat_position = current_position * self.meter_tuple[1] / 4
            is_strong = int(beat_position) in self.rhythm_generator.strong_beats

            is_near_end = (current_position + duration_ql) >= (total_ql * 0.9)
            is_phrase_boundary = is_near_end and measure_index % 2 == 1

            beat_index_int = int(beat_position)
            use_rest = self.pitch_selector.should_use_rest(
                measure_index, beat_index_int, is_strong, is_phrase_boundary
            )

            if use_rest:
                rest = self._create_rest(duration)
                notes.append(rest)
                self.pitch_selector.set_last_was_rest(True)
            else:
                note_pitch = self._get_note_pitch(
                    measure_index, beat_index_int, is_strong, rhythm_pattern,
                    note_index, is_cadence, is_near_end, cadence_type
                )

                abjad_pitch = self.lilypond_formatter.convert_to_abjad_pitch(note_pitch)
                note_string = self._create_note_string(abjad_pitch, duration)
                note = abjad.Note(note_string)
                notes.append(note)
                self.pitch_selector.set_last_was_rest(False)

            current_position += duration_ql

        return abjad.Container(notes)

    def _get_note_pitch(
        self, measure_index, beat_index_int, is_strong, rhythm_pattern,
        note_index, is_cadence, is_near_end, cadence_type
    ) -> str:
        """Obtiene el pitch para una nota según el contexto."""
        if is_cadence and is_near_end:
            is_penultimate = note_index == len(rhythm_pattern.durations) - 2
            is_final = note_index == len(rhythm_pattern.durations) - 1

            if cadence_type == "authentic":
                if is_penultimate:
                    return self.scale_manager.get_pitch_by_degree(7)
                elif is_final:
                    return self.scale_manager.get_pitch_by_degree(1)
            elif cadence_type == "half":
                if is_final:
                    return self.scale_manager.get_pitch_by_degree(5)
                elif is_penultimate:
                    return self.scale_manager.get_pitch_by_degree(4)

        note_pitch, _ = self.pitch_selector.select_melodic_pitch(
            measure_index, beat_index_int, is_strong, rhythm_pattern, note_index
        )
        return note_pitch

    def _create_rest(self, duration: Tuple[int, int]) -> abjad.Rest:
        """Crea un silencio con la duración especificada."""
        if duration[0] == 3:
            base_map = {8: 4, 16: 8, 4: 2, 32: 16, 2: 1}
            base_duration = base_map.get(duration[1], duration[1])
            rest_string = f"r{base_duration}."
        elif duration[0] == 1:
            rest_string = f"r{duration[1]}"
        else:
            rest_string = f"r{duration[1]}"

        return abjad.Rest(rest_string)

    def _create_note_string(self, abjad_pitch: str, duration: Tuple[int, int]) -> str:
        """Crea el string de nota para Abjad."""
        if duration[0] == 3:
            base_map = {8: 4, 16: 8, 4: 2, 32: 16, 2: 1}
            base_duration = base_map.get(duration[1], duration[1])
            return f"{abjad_pitch}{base_duration}."
        elif duration[0] == 1:
            return f"{abjad_pitch}{duration[1]}"
        else:
            return f"{abjad_pitch}{duration[1]}"

    def _create_measure_from_motif(
        self, motif: Motif, harmonic_func: HarmonicFunction, measure_index: int
    ) -> abjad.Container:
        """Crea un compás a partir de un motivo y una función armónica."""
        notes = []

        motif_duration_ql = sum(
            Fraction(num, denom) * 4
            for num, denom in motif.rhythm.durations
        )

        measure_duration_ql = Fraction(self.meter_tuple[0], self.meter_tuple[1]) * 4
        current_position = Fraction(0)

        for idx, (pitch_str, duration) in enumerate(
            zip(motif.pitches, motif.rhythm.durations)
        ):
            abjad_pitch = self.lilypond_formatter.convert_to_abjad_pitch(pitch_str)
            note_string = self._create_note_string(abjad_pitch, duration)
            note = abjad.Note(note_string)
            notes.append(note)
            current_position += Fraction(duration[0], duration[1]) * 4

        remaining_duration = measure_duration_ql - current_position

        while remaining_duration > 0:
            degree = random.choice(harmonic_func.chord_tones)
            pitch_str = self.scale_manager.get_pitch_by_degree(degree)
            abjad_pitch = self.lilypond_formatter.convert_to_abjad_pitch(pitch_str)

            if remaining_duration >= 1:
                duration_denom = 4
            elif remaining_duration >= Fraction(1, 2):
                duration_denom = 8
            else:
                duration_denom = 16

            note_string = f"{abjad_pitch}{duration_denom}"
            note = abjad.Note(note_string)
            notes.append(note)

            remaining_duration -= Fraction(1, duration_denom) * 4

        return abjad.Container(notes)

    def _add_staff_indications(self, staff: abjad.Staff):
        """Añade indicaciones de compás, clave y armadura al staff."""
        if len(staff) > 0 and len(staff[0]) > 0:
            abjad.attach(abjad.TimeSignature(self.meter_tuple), staff[0][0])
            abjad.attach(abjad.Clef("treble"), staff[0][0])

            key_sig = self.lilypond_formatter.create_key_signature()
            if key_sig:
                abjad.attach(key_sig, staff[0][0])

    def _add_ties_to_staff(self, staff: abjad.Staff, tie_probability: float = 0.15):
        """Añade ligaduras entre notas del mismo pitch."""
        all_leaves = list(abjad.select.leaves(staff))
        midpoint = self.num_measures // 2

        for i in range(len(all_leaves) - 1):
            current_leaf = all_leaves[i]
            next_leaf = all_leaves[i + 1]

            if not isinstance(current_leaf, abjad.Note) or not isinstance(
                next_leaf, abjad.Note
            ):
                continue

            if current_leaf.written_pitch != next_leaf.written_pitch:
                continue

            measure_idx = None
            for m_idx, container in enumerate(staff):
                if current_leaf in container:
                    measure_idx = m_idx
                    break

            if measure_idx is None:
                continue

            is_antecedent_end = measure_idx == midpoint - 1
            is_period_end = measure_idx == self.num_measures - 1

            if is_antecedent_end or is_period_end:
                container = staff[measure_idx]
                note_position = list(container).index(current_leaf)
                if note_position >= len(container) - 2:
                    continue

            duration_multiplier = 1.0
            if (
                current_leaf.written_duration.numerator >= 1
                and current_leaf.written_duration.denominator <= 4
            ):
                duration_multiplier = 1.5

            effective_probability = tie_probability * duration_multiplier

            if random.random() < effective_probability:
                abjad.attach(abjad.Tie(), current_leaf)
