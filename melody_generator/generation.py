"""
Métodos de generación de períodos musicales.
Implementa generación tradicional (cohesión rítmica) y jerárquica (formal).
"""

import random
from fractions import Fraction
from typing import List, Tuple, Optional

import abjad

from .models import Motif, HarmonicFunction, Phrase, Semiphrase, Period, ImpulseType
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
        impulse_type: ImpulseType = ImpulseType.TETIC,
    ):
        """
        Inicializa el generador de períodos.

        Args:
            impulse_type: Tipo de inicio (TETIC, ANACROUSTIC, ACEPHALOUS)
        """
        self.scale_manager = scale_manager
        self.harmony_manager = harmony_manager
        self.rhythm_generator = rhythm_generator
        self.pitch_selector = pitch_selector
        self.motif_generator = motif_generator
        self.lilypond_formatter = lilypond_formatter
        self.num_measures = num_measures
        self.meter_tuple = meter_tuple
        self.impulse_type = impulse_type

        # Calcular duración de anacrusa (típicamente 1 pulso antes del tiempo fuerte)
        self.anacrusis_duration = self._calculate_anacrusis_duration()

    def _calculate_anacrusis_duration(self) -> Tuple[int, int]:
        """
        Calcula la duración de la anacrusa según el compás.

        Para compases simples: 1 pulso (ej: negra en 4/4)
        Para compases compuestos: 1 subdivisión (ej: corchea en 6/8)

        Returns:
            Tupla (numerador, denominador) de la duración
        """
        num, denom = self.meter_tuple

        # Compases compuestos (6/8, 9/8, 12/8)
        if num in [6, 9, 12] and denom == 8:
            return (1, 8)  # Una corchea

        # Compases simples: un pulso
        return (1, denom)

    def generate_period(self) -> abjad.Staff:
        """
        Genera un período musical completo (método tradicional).

        Implementa la estructura de pregunta-respuesta con cadencias apropiadas.
        Genera un motivo rítmico base que se reutiliza para cohesión.

        Soporta tres tipos de inicio:
        - TETIC: Comienza en tiempo fuerte (compás completo)
        - ANACROUSTIC: Comienza con anacrusa (compás parcial antes del primero)
        - ACEPHALOUS: Comienza con silencio en tiempo fuerte
        """
        staff = abjad.Staff(name="Melodia")

        self.rhythm_generator.initialize_base_motif()

        # Manejar anacrusa (compás parcial antes del primer compás completo)
        if self.impulse_type == ImpulseType.ANACROUSTIC:
            anacrusis_container = self._create_anacrusis_measure()
            staff.append(anacrusis_container)
            # Añadir barra después de la anacrusa
            last_leaf = abjad.get.leaf(anacrusis_container, -1)
            if last_leaf:
                abjad.attach(abjad.BarLine("|"), last_leaf)

        midpoint = self.num_measures // 2

        for m_idx in range(self.num_measures):
            is_antecedent_end = m_idx == midpoint - 1
            is_period_end = m_idx == self.num_measures - 1

            # Para ACEPHALOUS, el primer compás comienza con silencio
            force_initial_rest = (
                self.impulse_type == ImpulseType.ACEPHALOUS and m_idx == 0
            )

            if is_period_end:
                container = self._create_measure(
                    m_idx, is_cadence=True, cadence_type="authentic",
                    force_initial_rest=force_initial_rest
                )
            elif is_antecedent_end:
                container = self._create_measure(
                    m_idx, is_cadence=True, cadence_type="half",
                    force_initial_rest=force_initial_rest
                )
            else:
                container = self._create_measure(
                    m_idx, is_cadence=False,
                    force_initial_rest=force_initial_rest
                )

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

    def _create_anacrusis_measure(self) -> abjad.Container:
        """
        Crea el compás de anacrusa (pickup).

        La anacrusa contiene típicamente una o pocas notas que preceden
        al primer tiempo fuerte del primer compás completo.
        """
        notes = []

        # Obtener pitch para la anacrusa (típicamente dominante o tónica)
        # Usar grado 5 (dominante) para crear expectativa hacia la tónica
        anacrusis_pitch = self.scale_manager.get_pitch_by_degree(5)
        abjad_pitch = self.lilypond_formatter.convert_to_abjad_pitch(anacrusis_pitch)

        # Crear nota con duración de anacrusa
        note_string = self._create_note_string(abjad_pitch, self.anacrusis_duration)
        note = abjad.Note(note_string)
        notes.append(note)

        # Guardar el pitch para continuidad melódica
        self.pitch_selector.last_pitch = anacrusis_pitch

        return abjad.Container(notes)

    def generate_period_hierarchical(
        self, return_structure: bool = False
    ) -> abjad.Staff | Tuple[abjad.Staff, Period]:
        """
        Genera un período musical con jerarquía formal verdadera.

        Implementa la estructura:
        Motivo → Frase (2 compases) → Semifrase (4 compases) → Período (8+ compases)

        Args:
            return_structure: Si True, retorna también la estructura Period

        Returns:
            Staff de Abjad, o tupla (Staff, Period) si return_structure=True
        """
        # 1. Crear el plan armónico completo
        harmonic_plan = self.harmony_manager.create_harmonic_progression(
            self.num_measures
        )

        # 2. Crear el motivo base generador
        base_motif = self.motif_generator.create_base_motif(
            harmonic_plan[0].degree
        )

        # 3. Construir la estructura jerárquica completa
        period = self._build_period(base_motif, harmonic_plan)

        # 4. Renderizar la estructura a Abjad Staff
        staff = self._render_period_to_staff(period)

        if return_structure:
            return staff, period
        return staff

    def _build_phrase(
        self,
        base_motif: Motif,
        harmonic_funcs: List[HarmonicFunction],
        measure_start: int,
        is_first_phrase: bool = False,
        variation_type: str = "auto",
    ) -> Phrase:
        """
        Construye una Phrase (2 compases) a partir de un motivo base.

        Args:
            base_motif: Motivo generador
            harmonic_funcs: Funciones armónicas para los 2 compases
            measure_start: Índice del compás inicial
            is_first_phrase: Si es la primera frase del período
            variation_type: Tipo de variación a aplicar

        Returns:
            Phrase con motivo original y variación
        """
        # Primer compás: motivo original o variación según contexto
        if is_first_phrase:
            motif_1 = base_motif
        else:
            motif_1 = self.motif_generator.apply_motif_variation(
                base_motif, variation_type=variation_type
            )

        # Segundo compás: variación del motivo
        motif_2 = self.motif_generator.apply_motif_variation(
            base_motif, variation_type=variation_type
        )

        return Phrase(
            motif=motif_1,
            variation=motif_2,
            harmonic_progression=harmonic_funcs,
            measure_range=(measure_start, measure_start + 2),
            variation_type=variation_type,
        )

    def _build_semiphrase(
        self,
        base_motif: Motif,
        harmonic_funcs: List[HarmonicFunction],
        measure_start: int,
        function: str,
        is_first_semiphrase: bool = False,
    ) -> Semiphrase:
        """
        Construye una Semiphrase (típicamente 4 compases).

        Args:
            base_motif: Motivo generador
            harmonic_funcs: Funciones armónicas para la semifrase
            measure_start: Índice del compás inicial
            function: "antecedent" o "consequent"
            is_first_semiphrase: Si es la primera semifrase del período

        Returns:
            Semiphrase con sus frases constituyentes
        """
        phrases = []
        num_measures = len(harmonic_funcs)
        num_phrases = (num_measures + 1) // 2

        # Determinar tipo de cadencia
        cadence_type = "half" if function == "antecedent" else "authentic"

        # Determinar variaciones según posición
        for phrase_idx in range(num_phrases):
            local_start = phrase_idx * 2
            local_end = min(local_start + 2, num_measures)
            phrase_harmonics = harmonic_funcs[local_start:local_end]

            # Primera frase de la primera semifrase: usar motivo original
            is_first = is_first_semiphrase and phrase_idx == 0

            # Última frase: variación más estricta para coherencia cadencial
            if phrase_idx == num_phrases - 1:
                var_type = "strict"
            elif function == "consequent":
                var_type = "moderate"
            else:
                var_type = "auto"

            phrase = self._build_phrase(
                base_motif,
                phrase_harmonics,
                measure_start + local_start,
                is_first_phrase=is_first,
                variation_type=var_type,
            )
            phrases.append(phrase)

        return Semiphrase(
            phrases=phrases,
            function=function,
            cadence_type=cadence_type,
            measure_range=(measure_start, measure_start + num_measures),
        )

    def _build_period(
        self, base_motif: Motif, harmonic_plan: List[HarmonicFunction]
    ) -> Period:
        """
        Construye un Period completo con estructura jerárquica.

        Args:
            base_motif: Motivo generador de todo el período
            harmonic_plan: Plan armónico completo

        Returns:
            Period con antecedente y consecuente
        """
        midpoint = self.num_measures // 2

        # Construir antecedente (primera mitad, termina en V)
        antecedent_harmonics = harmonic_plan[:midpoint]
        antecedent = self._build_semiphrase(
            base_motif,
            antecedent_harmonics,
            measure_start=0,
            function="antecedent",
            is_first_semiphrase=True,
        )

        # Construir consecuente (segunda mitad, termina en I)
        consequent_harmonics = harmonic_plan[midpoint:]
        consequent = self._build_semiphrase(
            base_motif,
            consequent_harmonics,
            measure_start=midpoint,
            function="consequent",
            is_first_semiphrase=False,
        )

        return Period(
            antecedent=antecedent,
            consequent=consequent,
            total_measures=self.num_measures,
            base_motif=base_motif,
            harmonic_plan=harmonic_plan,
        )

    def _render_period_to_staff(self, period: Period) -> abjad.Staff:
        """
        Renderiza un Period a un Abjad Staff.

        Args:
            period: Estructura Period a renderizar

        Returns:
            Staff de Abjad con la melodía generada
        """
        staff = abjad.Staff(name="Melodia_Hierarchical")

        # Obtener todos los motivos en orden
        all_motifs = period.get_all_motifs()

        # Renderizar cada motivo como un compás
        for measure_idx, motif in enumerate(all_motifs):
            if measure_idx >= self.num_measures:
                break

            harmonic_func = period.harmonic_plan[measure_idx]
            measure_container = self._create_measure_from_motif(
                motif, harmonic_func, measure_idx
            )

            staff.append(measure_container)

            # Añadir barras de compás
            last_leaf = abjad.get.leaf(measure_container, -1)
            if last_leaf:
                if measure_idx < self.num_measures - 1:
                    abjad.attach(abjad.BarLine("|"), last_leaf)
                else:
                    abjad.attach(abjad.BarLine("|."), last_leaf)

        self._add_staff_indications(staff)

        return staff

    def _create_measure(
        self,
        measure_index: int,
        is_cadence: bool = False,
        cadence_type: str = "authentic",
        force_initial_rest: bool = False,
    ) -> abjad.Container:
        """
        Crea un compás basado en la estructura de pulsos y la teoría armónica.

        Args:
            measure_index: Índice del compás
            is_cadence: Si es un compás cadencial
            cadence_type: Tipo de cadencia ("authentic" o "half")
            force_initial_rest: Si True, fuerza un silencio en el primer tiempo
                              (para inicio acéfalo)
        """
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

            # Forzar silencio inicial para inicio acéfalo
            if force_initial_rest and note_index == 0:
                use_rest = True
            else:
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
        """
        Obtiene el pitch para una nota según el contexto.

        Cadencias según teoría clásica:
        - Auténtica (V→I): La melodía usa notas del acorde de dominante (5, 7, 2)
          resolviendo a la tónica. Típicamente: 5→1 o 2→1 (descendente) o 7→1 (ascendente)
        - Semicadencia (→V): La melodía termina en nota del acorde de dominante
        """
        if is_cadence and is_near_end:
            num_notes = len(rhythm_pattern.durations)
            is_antepenultimate = note_index == num_notes - 3
            is_penultimate = note_index == num_notes - 2
            is_final = note_index == num_notes - 1

            if cadence_type == "authentic":
                # Cadencia auténtica: V → I
                # Gesto melódico típico: 5→2→1 o 4→7→1 o 5→5→1
                if is_antepenultimate and num_notes >= 3:
                    # Tercera nota desde el final: subdominante o dominante
                    return self.scale_manager.get_pitch_by_degree(5)
                elif is_penultimate:
                    # Penúltima: nota de dominante que resuelve a tónica
                    # Usar 2 (supertónica) para resolución descendente 2→1
                    return self.scale_manager.get_pitch_by_degree(2)
                elif is_final:
                    # Final: tónica
                    return self.scale_manager.get_pitch_by_degree(1)

            elif cadence_type == "half":
                # Semicadencia: termina en V
                # Gesto melódico típico: IV→V (4→5)
                if is_antepenultimate and num_notes >= 3:
                    return self.scale_manager.get_pitch_by_degree(1)
                elif is_penultimate:
                    # Penúltima: subdominante
                    return self.scale_manager.get_pitch_by_degree(4)
                elif is_final:
                    # Final: dominante
                    return self.scale_manager.get_pitch_by_degree(5)

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
