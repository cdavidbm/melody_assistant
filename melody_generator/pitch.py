"""
Selección de tonos y control del contorno melódico.
Implementa reglas teóricas de movimiento melódico con sistema de scoring multi-criterio.
"""

import random
from typing import Tuple, Optional, List, Dict, TYPE_CHECKING

from music21 import pitch, interval

from .models import (
    NoteFunction,
    RhythmicPattern,
    MelodicContour,
    ImpulseType,
)
from .scales import ScaleManager
from .harmony import HarmonyManager
from .scoring import (
    MelodicScorer,
    PhraseContour,
    PhrasePosition,
    MetricStrength,
    NoteCandidate,
)
from .memory import (
    DecisionMemory,
    Decision,
    DecisionType,
    Alternative,
    ScoreBreakdown,
    HarmonicContext,
    MelodicContext,
    MetricContext,
)

if TYPE_CHECKING:
    from .markov import MelodicMarkovModel, EnhancedMelodicMarkovModel


class PitchSelector:
    """
    Selecciona tonos melódicos según las reglas de la teoría musical.

    Usa un sistema de scoring multi-criterio que considera:
    - Conducción de voces (movimiento por grado conjunto preferido)
    - Compatibilidad armónica (notas del acorde en tiempos fuertes)
    - Contorno melódico planificado (curva de la frase)
    - Resolución de notas de tendencia
    - Sugerencias de Markov (cuando disponible)
    - Variedad melódica (evitar repetición)
    - Posición en el rango (preferir centro)
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
        markov_model: Optional["MelodicMarkovModel"] = None,
        markov_weight: float = 0.5,
        scoring_temperature: float = 0.3,
        decision_memory: Optional[DecisionMemory] = None,
    ):
        """
        Inicializa el selector de tonos.

        Args:
            scale_manager: Gestor de escalas y modos
            harmony_manager: Gestor de armonía
            contour: Configuración del contorno melódico
            num_measures: Número de compases
            max_interval: Intervalo máximo permitido (semitonos)
            use_tenoris: Si usar técnica de tenoris
            tenoris_probability: Probabilidad de tenoris
            infraction_rate: Tasa de infracciones ornamentales
            use_rests: Si usar silencios
            rest_probability: Probabilidad de silencios
            impulse_type: Tipo de impulso (tético, anacrúsico, acéfalo)
            meter_tuple: Métrica (numerador, denominador)
            markov_model: Modelo de Markov opcional para sugerencias melódicas
            markov_weight: Peso de influencia del modelo Markov (0.0-1.0)
            scoring_temperature: Aleatoriedad en selección (0=determinista, 1=muy aleatorio)
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
        self.markov_model = markov_model
        self.markov_weight = markov_weight
        self.scoring_temperature = scoring_temperature

        # Sistema de memoria para decisiones
        self.decision_memory = decision_memory
        self._note_index = 0  # Índice global de notas

        # Estado interno
        self.current_octave = 4
        self.last_pitch: Optional[str] = None
        self.last_interval_direction: Optional[int] = None
        self.infraction_pending_compensation = False
        self.last_was_rest = False
        self.must_recover_leap = False
        self.pending_tendency_resolution: Optional[int] = None  # Grado que debe resolver

        # Control del clímax
        self.climax_measure = int(num_measures * contour.climax_position)
        self.climax_reached = False
        self.current_highest_pitch: Optional[str] = None

        # Contexto métrico actual (para Markov mejorado)
        self._current_is_strong_beat = False

        # Inicializar sistema de scoring
        self._init_scorer()

        # Plan de contorno por frase (se inicializa al empezar cada frase)
        self.current_phrase_contour: Optional[PhraseContour] = None
        self.notes_in_current_phrase = 0

    def _init_scorer(self):
        """Inicializa el sistema de scoring multi-criterio."""
        # Obtener rango melódico del scale_manager
        melodic_range = (
            int(self.scale_manager.melodic_range_bottom.midi),
            int(self.scale_manager.melodic_range_top.midi),
        )

        # Notas de tendencia según el modo
        tendency_tones = self._get_tendency_tones()

        # Configurar pesos según estilo deseado
        # Los pesos pueden ajustarse para diferentes estilos
        weights = {
            "voice_leading": 0.28,  # Conducción de voces (muy importante)
            "harmonic": 0.22,       # Compatibilidad armónica
            "contour": 0.15,        # Seguir contorno planificado
            "tendency": 0.12,       # Resolver notas de tendencia
            "markov": 0.10 if self.markov_model else 0.0,  # Markov si disponible
            "variety": 0.08,        # Evitar repetición
            "range": 0.05,          # Preferir centro del rango
        }

        # Normalizar pesos si Markov no está disponible
        if not self.markov_model:
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}

        self.scorer = MelodicScorer(
            scale_degrees=[1, 2, 3, 4, 5, 6, 7],
            chord_tones=[1, 3, 5],  # Se actualiza dinámicamente
            tendency_tones=tendency_tones,
            melodic_range=melodic_range,
            weights=weights,
        )

    def _get_tendency_tones(self) -> Dict[int, int]:
        """Obtiene el mapeo de notas de tendencia según el modo."""
        mode = self.scale_manager.mode

        # Notas de tendencia comunes
        tendency = {
            7: 1,  # Sensible → Tónica (ascendente)
            4: 3,  # Cuarto grado → Mediante (descendente)
        }

        # Ajustes por modo
        if mode == "phrygian":
            tendency[2] = 1  # Segunda bemol → Tónica
        elif mode == "lydian":
            tendency[4] = 5  # Cuarta aumentada → Quinta
        elif mode == "locrian":
            tendency[5] = 4  # Quinta disminuida → Cuarta

        return tendency

    def plan_phrase_contour(
        self,
        phrase_length: int,
        is_antecedent: bool = True,
        start_degree: int = 1,
    ):
        """
        Planifica el contorno para una frase completa.

        Args:
            phrase_length: Número de notas en la frase
            is_antecedent: True para antecedente, False para consecuente
            start_degree: Grado inicial de la frase
        """
        # Determinar grado del clímax según posición en período
        if is_antecedent:
            # Antecedente: clímax en grado 5 (dominante)
            climax_degree = 5
            end_degree = 5 if phrase_length >= 4 else 2  # Semicadencia
            climax_position = 0.6
        else:
            # Consecuente: clímax más alto, termina en tónica
            climax_degree = 6 if self.climax_reached else 5
            end_degree = 1  # Cadencia auténtica
            climax_position = 0.5

        self.current_phrase_contour = PhraseContour(
            length=phrase_length,
            start_degree=start_degree,
            climax_position=climax_position,
            climax_degree=climax_degree,
            end_degree=end_degree,
            direction=1,  # Generalmente ascendente hacia clímax
        )
        self.current_phrase_contour.plan_targets()
        self.notes_in_current_phrase = 0

    def _get_phrase_position(self, note_index: int, phrase_length: int) -> PhrasePosition:
        """Determina la posición dentro de la frase."""
        if phrase_length <= 0:
            return PhrasePosition.MIDDLE

        progress = note_index / max(1, phrase_length - 1)

        if note_index == 0:
            return PhrasePosition.BEGINNING
        elif note_index == phrase_length - 1:
            return PhrasePosition.FINAL
        elif progress >= 0.85:
            return PhrasePosition.CADENCE
        elif abs(progress - self.contour.climax_position) < 0.1:
            return PhrasePosition.CLIMAX
        elif progress > self.contour.climax_position:
            return PhrasePosition.POST_CLIMAX
        elif progress > self.contour.climax_position - 0.2:
            return PhrasePosition.APPROACHING_CLIMAX
        else:
            return PhrasePosition.MIDDLE

    def _get_metric_strength(self, beat_index: int, is_strong_beat: bool) -> MetricStrength:
        """Determina la fuerza métrica del pulso."""
        beats_per_measure = self.meter_tuple[0]

        if beat_index == 0:
            return MetricStrength.STRONG
        elif is_strong_beat:
            return MetricStrength.SEMI_STRONG
        elif beat_index < beats_per_measure:
            return MetricStrength.WEAK
        else:
            return MetricStrength.SUBDIVISION

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
        Selecciona el tono melódico usando el sistema de scoring multi-criterio.

        El sistema evalúa todos los candidatos posibles y selecciona basándose en:
        - Conducción de voces (intervalos pequeños preferidos)
        - Compatibilidad armónica (notas del acorde en tiempos fuertes)
        - Contorno melódico planificado
        - Resolución de notas de tendencia
        - Sugerencias de Markov (si disponible)
        - Variedad y rango

        Returns:
            Tupla de (nota, función)
        """
        harmonic_function = self.harmony_manager.get_harmonic_function(
            measure_index, beat_index
        )
        chord_tones = self.harmony_manager.get_chord_tones_for_function(
            harmonic_function
        )

        # Actualizar chord_tones en el scorer
        self.scorer.chord_tones = chord_tones

        # Determinar contexto métrico y de frase
        metric_strength = self._get_metric_strength(beat_index, is_strong_beat)
        self._current_is_strong_beat = is_strong_beat

        # Determinar posición en la frase
        phrase_length = self.current_phrase_contour.length if self.current_phrase_contour else 16
        phrase_position = self._get_phrase_position(
            self.notes_in_current_phrase, phrase_length
        )

        # Obtener grado objetivo del contorno planificado
        target_degree = None
        if (
            self.current_phrase_contour
            and self.notes_in_current_phrase < len(self.current_phrase_contour.target_degrees)
        ):
            target_degree = self.current_phrase_contour.target_degrees[
                self.notes_in_current_phrase
            ]

        # Determinar si debe ser nota estructural
        should_be_structural = is_strong_beat

        # Sistema de infracción (permite ornamentales en tiempos fuertes ocasionalmente)
        if (
            random.random() < self.infraction_rate
            and not self.infraction_pending_compensation
        ):
            should_be_structural = not should_be_structural
            self.infraction_pending_compensation = True
        elif self.infraction_pending_compensation:
            should_be_structural = True
            self.infraction_pending_compensation = False

        # Considerar tenoris (nota pedal en grado 5)
        use_tenoris_now = (
            self.use_tenoris
            and should_be_structural
            and random.random() < self.tenoris_probability
            and not is_strong_beat
        )

        if use_tenoris_now:
            degree = 5
            function = NoteFunction.STRUCTURAL
            note_pitch = self.scale_manager.get_pitch_by_degree(degree, self.current_octave)
        else:
            # SELECCIÓN POR SCORING MULTI-CRITERIO
            note_pitch, degree, function = self._select_by_scoring(
                metric_strength=metric_strength,
                phrase_position=phrase_position,
                target_degree=target_degree,
                chord_tones=chord_tones,
                should_be_structural=should_be_structural,
                measure_index=measure_index,
                beat_index=beat_index,
                is_strong_beat=is_strong_beat,
                harmonic_function=str(harmonic_function) if harmonic_function else None,
            )

        # Ajustar octava para contorno
        if self.last_pitch:
            note_pitch = self._adjust_octave_for_contour(
                note_pitch, measure_index, is_structural=should_be_structural
            )

        # Actualizar historial de Markov
        if self.markov_model and self.last_pitch:
            last_p = pitch.Pitch(self.last_pitch)
            current_p = pitch.Pitch(note_pitch)
            actual_interval = int(current_p.ps - last_p.ps)

            # Si es modelo mejorado, usar update con grado, métrica y dirección
            if hasattr(self.markov_model, 'get_degree_probabilities'):
                direction = 1 if actual_interval > 0 else (-1 if actual_interval < 0 else 0)
                metric = "strong" if is_strong_beat else "weak"
                self.markov_model.update_history(degree, metric, direction)
            else:
                # Modelo clásico: solo intervalo
                self.markov_model.update_history(actual_interval)

        # Actualizar estado
        self.last_pitch = note_pitch
        self.scorer.update_history(degree)
        self.notes_in_current_phrase += 1

        # Verificar notas de tendencia
        if self.scale_manager.is_tendency_tone(degree):
            self.pending_tendency_resolution = degree
        elif self.pending_tendency_resolution is not None:
            self.pending_tendency_resolution = None

        return note_pitch, function

    def _select_by_scoring(
        self,
        metric_strength: MetricStrength,
        phrase_position: PhrasePosition,
        target_degree: Optional[int],
        chord_tones: List[int],
        should_be_structural: bool,
        measure_index: int,
        beat_index: int = 0,
        is_strong_beat: bool = False,
        harmonic_function: Optional[str] = None,
    ) -> Tuple[str, int, NoteFunction]:
        """
        Selecciona una nota usando el sistema de scoring multi-criterio.

        Registra la decisión en DecisionMemory si está disponible.

        Returns:
            Tupla de (pitch_str, degree, function)
        """
        # Función para obtener pitch por grado (pasada al scorer)
        def get_pitch_func(deg: int, octave: int) -> str:
            return self.scale_manager.get_pitch_by_degree(deg, octave)

        # Generar y evaluar todos los candidatos
        candidates = self.scorer.generate_candidates(
            last_pitch=self.last_pitch,
            target_degree=target_degree,
            metric_strength=metric_strength,
            phrase_position=phrase_position,
            get_pitch_func=get_pitch_func,
        )

        if not candidates:
            # Fallback: usar tónica
            degree = 1
            pitch_str = self.scale_manager.get_pitch_by_degree(degree, self.current_octave)
            return pitch_str, degree, NoteFunction.STRUCTURAL

        # Añadir scores de Markov si está disponible
        if self.markov_model:
            markov_probs = self._get_markov_probabilities()
            self.scorer.add_markov_scores(candidates, markov_probs)

            # Recalcular totales con Markov incluido
            for candidate in candidates:
                candidate.calculate_total(self.scorer.weights)

            # Reordenar
            candidates.sort(key=lambda c: c.total_score, reverse=True)

        # Ajustar scores para notas estructurales vs ornamentales
        if should_be_structural:
            # Boost a notas del acorde
            for c in candidates:
                if c.degree in chord_tones:
                    c.total_score *= 1.3
            candidates.sort(key=lambda c: c.total_score, reverse=True)

        # Seleccionar con algo de aleatoriedad controlada
        selected = self.scorer.select_best(
            candidates,
            temperature=self.scoring_temperature,
        )

        # Determinar función
        function = (
            NoteFunction.STRUCTURAL
            if selected.degree in chord_tones and should_be_structural
            else NoteFunction.PASSING
        )

        # REGISTRAR DECISIÓN EN MEMORIA
        if self.decision_memory is not None:
            self._record_decision(
                selected=selected,
                candidates=candidates,
                measure_index=measure_index,
                beat_index=beat_index,
                is_strong_beat=is_strong_beat,
                chord_tones=chord_tones,
                harmonic_function=harmonic_function,
                phrase_position=phrase_position,
                target_degree=target_degree,
            )

        return selected.pitch_str, selected.degree, function

    def _record_decision(
        self,
        selected: NoteCandidate,
        candidates: List[NoteCandidate],
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        chord_tones: List[int],
        harmonic_function: Optional[str],
        phrase_position: PhrasePosition,
        target_degree: Optional[int],
    ):
        """
        Registra una decisión de pitch en la memoria.

        Guarda el contexto completo para permitir correcciones quirúrgicas.
        """
        # Crear desglose de scores (usando atributos individuales de NoteCandidate)
        score_breakdown = ScoreBreakdown(
            voice_leading=selected.voice_leading_score,
            harmonic=selected.harmonic_score,
            contour=selected.contour_score,
            tendency=selected.tendency_score,
            markov=selected.markov_score,
            variety=selected.variety_score,
            range=selected.range_score,
        )

        # Crear alternativas (excluyendo la seleccionada)
        alternatives = []
        for c in candidates:
            if c.pitch_str != selected.pitch_str:
                alt_breakdown = ScoreBreakdown(
                    voice_leading=c.voice_leading_score,
                    harmonic=c.harmonic_score,
                    contour=c.contour_score,
                    tendency=c.tendency_score,
                    markov=c.markov_score,
                    variety=c.variety_score,
                    range=c.range_score,
                )
                alternatives.append(Alternative(
                    value=c.pitch_str,
                    score=c.total_score,
                    score_breakdown=alt_breakdown,
                ))

        # Calcular dirección melódica
        direction = 0
        prev_interval = None
        if self.last_pitch:
            try:
                last_p = pitch.Pitch(self.last_pitch)
                curr_p = pitch.Pitch(selected.pitch_str)
                prev_interval = int(curr_p.ps - last_p.ps)
                direction = 1 if prev_interval > 0 else (-1 if prev_interval < 0 else 0)
            except Exception:
                pass

        # Contexto armónico
        harmonic_ctx = HarmonicContext(
            chord_degree=chord_tones[0] if chord_tones else 1,
            chord_tones=chord_tones,
            function=harmonic_function or "unknown",
        )

        # Contexto melódico
        melodic_ctx = MelodicContext(
            previous_pitch=self.last_pitch,
            previous_interval=prev_interval,
            direction=direction,
            phrase_position=self.notes_in_current_phrase / max(1, self.current_phrase_contour.length) if self.current_phrase_contour else 0.0,
            is_climax=(phrase_position == PhrasePosition.CLIMAX),
            contour_target=target_degree,
        )

        # Contexto métrico
        metric_ctx = MetricContext(
            measure=measure_index + 1,  # 1-indexed para el usuario
            beat=float(beat_index + 1),  # 1-indexed
            beat_strength="strong" if is_strong_beat else "weak",
            subdivision=1,  # TODO: calcular subdivisión real
            is_downbeat=(beat_index == 0),
            is_phrase_start=(self.notes_in_current_phrase == 0),
            is_phrase_end=False,  # Se actualizará después si es necesario
        )

        # Crear y registrar decisión
        decision = Decision(
            decision_type=DecisionType.PITCH,
            measure=measure_index + 1,
            beat=float(beat_index + 1),
            index=self._note_index,
            chosen_value=selected.pitch_str,
            chosen_score=selected.total_score,
            score_breakdown=score_breakdown,
            alternatives=alternatives,
            harmonic_context=harmonic_ctx,
            melodic_context=melodic_ctx,
            metric_context=metric_ctx,
        )

        self.decision_memory.record_decision(decision)
        self._note_index += 1

    def _get_markov_probabilities(self) -> Dict[int, float]:
        """
        Obtiene probabilidades de Markov para cada grado de la escala.

        Si el modelo es EnhancedMelodicMarkovModel, usa probabilidades
        nativas por grado. Si es MelodicMarkovModel clásico, convierte
        intervalos a grados.
        """
        if not self.markov_model or not self.last_pitch:
            return {}

        # Verificar si es modelo mejorado (tiene método get_degree_probabilities)
        if hasattr(self.markov_model, 'get_degree_probabilities'):
            # Modelo mejorado: usar probabilidades nativas por grado
            metric = "strong" if self._current_is_strong_beat else "weak"
            return self.markov_model.get_degree_probabilities(current_metric=metric)

        # Modelo clásico: convertir intervalos a grados
        last_degree = self.scale_manager.pitch_to_degree(self.last_pitch)
        if last_degree is None:
            return {}

        probs = {}

        # Para cada grado posible, calcular la probabilidad basada en el intervalo
        for target_degree in range(1, 8):
            # Calcular movimiento en grados
            degree_diff = target_degree - last_degree

            # Convertir a semitonos aproximados (asumiendo escala diatónica)
            semitone_approx = self._degree_movement_to_semitones(degree_diff)

            # Obtener probabilidad del modelo Markov
            prob = self.markov_model.get_probability(semitone_approx)
            probs[target_degree] = prob

        return probs

    def _degree_movement_to_semitones(self, degree_movement: int) -> int:
        """
        Convierte un movimiento en grados a semitonos aproximados.

        Usa el promedio de una escala diatónica:
        - 1 grado ≈ 2 semitonos (segunda mayor promedio)
        - 2 grados ≈ 3.5 semitonos (tercera)
        - etc.
        """
        direction = 1 if degree_movement >= 0 else -1
        abs_movement = abs(degree_movement)

        # Mapeo aproximado grados → semitonos
        semitone_map = {
            0: 0,
            1: 2,   # Segunda mayor
            2: 4,   # Tercera mayor
            3: 5,   # Cuarta justa
            4: 7,   # Quinta justa
            5: 9,   # Sexta mayor
            6: 11,  # Séptima mayor
            7: 12,  # Octava
        }

        semitones = semitone_map.get(abs_movement % 8, 2)
        return direction * semitones

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

    def reset_for_new_generation(self):
        """Reinicia el estado para una nueva generación."""
        self._note_index = 0
        self.last_pitch = None
        self.last_interval_direction = None
        self.infraction_pending_compensation = False
        self.last_was_rest = False
        self.must_recover_leap = False
        self.pending_tendency_resolution = None
        self.climax_reached = False
        self.current_highest_pitch = None
        self.notes_in_current_phrase = 0
        self.current_phrase_contour = None
        if self.decision_memory:
            self.decision_memory.clear()

    def set_decision_memory(self, memory: DecisionMemory):
        """Establece la memoria de decisiones."""
        self.decision_memory = memory
        self._note_index = 0

    def _resolve_tendency_tone(self, tendency_degree: int) -> int:
        """
        Resuelve una nota de tendencia según la teoría clásica.

        Resoluciones:
        - Grado 7 (sensible) → Grado 1 (tónica) - ASCENDENTE
        - Grado 4 → Grado 3 - DESCENDENTE

        Args:
            tendency_degree: Grado de la nota de tendencia (7 o 4)

        Returns:
            Grado de resolución
        """
        if tendency_degree == 7:
            # La sensible resuelve HACIA ARRIBA a la tónica
            return 1
        elif tendency_degree == 4:
            # El cuarto grado resuelve HACIA ABAJO a la mediante
            return 3
        else:
            # Para otros grados, movimiento por grado conjunto descendente
            return tendency_degree - 1 if tendency_degree > 1 else 7

    def _semitones_to_degree_movement(self, semitones: int) -> int:
        """
        Convierte un intervalo en semitonos a un movimiento en grados de escala.

        Mapeo aproximado (asumiendo escala diatónica promedio):
        - 0 semitonos → 0 grados (unísono)
        - 1-2 semitonos → 1 grado (segunda)
        - 3-4 semitonos → 2 grados (tercera)
        - 5-6 semitonos → 3 grados (cuarta)
        - 7-8 semitonos → 4 grados (quinta)
        - 9-10 semitonos → 5 grados (sexta)
        - 11-12 semitonos → 6-7 grados (séptima/octava)

        Args:
            semitones: Intervalo en semitonos (puede ser negativo)

        Returns:
            Movimiento en grados de escala (1 = segunda, 2 = tercera, etc.)
        """
        direction = 1 if semitones >= 0 else -1
        abs_semitones = abs(semitones)

        # Mapeo de semitonos a grados
        if abs_semitones == 0:
            degree_movement = 0
        elif abs_semitones <= 2:
            degree_movement = 1  # Segunda
        elif abs_semitones <= 4:
            degree_movement = 2  # Tercera
        elif abs_semitones <= 6:
            degree_movement = 3  # Cuarta
        elif abs_semitones <= 8:
            degree_movement = 4  # Quinta
        elif abs_semitones <= 10:
            degree_movement = 5  # Sexta
        else:
            degree_movement = 6  # Séptima

        return direction * degree_movement
