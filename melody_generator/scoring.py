"""
Sistema de scoring para seleccion de notas melodicas.
Evalua candidatos segun multiples criterios teoricos y estilisticos.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
import random

from music21 import pitch, interval


class PhrasePosition(Enum):
    """Posicion dentro de la frase."""
    BEGINNING = "beginning"      # Primeras notas
    MIDDLE = "middle"            # Desarrollo
    APPROACHING_CLIMAX = "approaching_climax"
    CLIMAX = "climax"
    POST_CLIMAX = "post_climax"
    CADENCE = "cadence"          # Preparacion cadencial
    FINAL = "final"              # Nota final


class MetricStrength(Enum):
    """Fuerza metrica del pulso."""
    STRONG = "strong"           # Tiempo 1
    SEMI_STRONG = "semi_strong" # Tiempo 3 en 4/4
    WEAK = "weak"               # Tiempos debiles
    SUBDIVISION = "subdivision"  # Subdivisiones


@dataclass
class NoteCandidate:
    """Un candidato de nota con su puntuacion."""
    degree: int                  # Grado de la escala (1-7)
    octave: int                  # Octava
    pitch_str: str               # Representacion string (ej: "C4")

    # Scores individuales (0.0 - 1.0)
    voice_leading_score: float = 0.0
    harmonic_score: float = 0.0
    contour_score: float = 0.0
    tendency_score: float = 0.0
    markov_score: float = 0.0
    variety_score: float = 0.0
    range_score: float = 0.0

    # Score total ponderado
    total_score: float = 0.0

    def calculate_total(self, weights: Dict[str, float]) -> float:
        """Calcula score total con pesos personalizados."""
        self.total_score = (
            self.voice_leading_score * weights.get("voice_leading", 0.25) +
            self.harmonic_score * weights.get("harmonic", 0.20) +
            self.contour_score * weights.get("contour", 0.15) +
            self.tendency_score * weights.get("tendency", 0.15) +
            self.markov_score * weights.get("markov", 0.10) +
            self.variety_score * weights.get("variety", 0.10) +
            self.range_score * weights.get("range", 0.05)
        )
        return self.total_score


@dataclass
class PhraseContour:
    """Plan de contorno para una frase."""
    length: int                          # Longitud en notas
    start_degree: int = 1                # Grado inicial
    climax_position: float = 0.7         # Posicion del climax (0-1)
    climax_degree: int = 5               # Grado objetivo del climax
    end_degree: int = 1                  # Grado final
    direction: int = 1                   # 1=ascendente, -1=descendente inicial

    # Grados objetivo por posicion (se calcula)
    target_degrees: List[int] = field(default_factory=list)

    def plan_targets(self):
        """Planifica los grados objetivo para cada posicion."""
        self.target_degrees = []
        climax_idx = int(self.length * self.climax_position)

        for i in range(self.length):
            if i == 0:
                self.target_degrees.append(self.start_degree)
            elif i == self.length - 1:
                self.target_degrees.append(self.end_degree)
            elif i == climax_idx:
                self.target_degrees.append(self.climax_degree)
            elif i < climax_idx:
                # Interpolacion hacia climax
                progress = i / climax_idx
                target = self.start_degree + int(
                    (self.climax_degree - self.start_degree) * progress
                )
                self.target_degrees.append(max(1, min(7, target)))
            else:
                # Interpolacion desde climax hacia final
                progress = (i - climax_idx) / (self.length - 1 - climax_idx)
                target = self.climax_degree + int(
                    (self.end_degree - self.climax_degree) * progress
                )
                self.target_degrees.append(max(1, min(7, target)))


class MelodicScorer:
    """
    Evalua candidatos de notas segun criterios teoricos.

    Implementa un sistema de scoring multi-criterio que combina:
    - Conduccion de voces (voice leading)
    - Compatibilidad armonica
    - Contorno melodico planificado
    - Resolucion de notas de tendencia
    - Sugerencias de Markov
    - Variedad melodica
    - Rango vocal
    """

    def __init__(
        self,
        scale_degrees: List[int],
        chord_tones: List[int],
        tendency_tones: Dict[int, int],  # {grado: resolucion}
        melodic_range: Tuple[int, int],  # (min_midi, max_midi)
        weights: Optional[Dict[str, float]] = None,
    ):
        """
        Inicializa el scorer.

        Args:
            scale_degrees: Grados disponibles (usualmente 1-7)
            chord_tones: Grados que son notas del acorde actual
            tendency_tones: Mapeo de notas de tendencia a sus resoluciones
            melodic_range: Rango MIDI permitido (min, max)
            weights: Pesos personalizados para cada criterio
        """
        self.scale_degrees = scale_degrees
        self.chord_tones = chord_tones
        self.tendency_tones = tendency_tones
        self.melodic_range = melodic_range

        # Pesos por defecto (suman 1.0)
        self.weights = weights or {
            "voice_leading": 0.25,
            "harmonic": 0.20,
            "contour": 0.15,
            "tendency": 0.15,
            "markov": 0.10,
            "variety": 0.10,
            "range": 0.05,
        }

        # Historial para variedad
        self.recent_degrees: List[int] = []
        self.max_history = 8

    def generate_candidates(
        self,
        last_pitch: Optional[str],
        target_degree: Optional[int],
        metric_strength: MetricStrength,
        phrase_position: PhrasePosition,
        get_pitch_func,  # Funcion para obtener pitch por grado
    ) -> List[NoteCandidate]:
        """
        Genera y evalua todos los candidatos posibles.

        Args:
            last_pitch: Ultima nota tocada (None si es primera)
            target_degree: Grado objetivo del contorno (None si no hay plan)
            metric_strength: Fuerza del pulso actual
            phrase_position: Posicion en la frase
            get_pitch_func: Funcion(degree, octave) -> pitch_str

        Returns:
            Lista de candidatos ordenados por score (mejor primero)
        """
        candidates = []

        # Determinar octavas a considerar
        if last_pitch:
            last_p = pitch.Pitch(last_pitch)
            base_octave = last_p.octave
            octaves = [base_octave - 1, base_octave, base_octave + 1]
        else:
            octaves = [4]  # Octava por defecto

        # Generar candidatos para cada grado y octava
        for degree in self.scale_degrees:
            for octave in octaves:
                try:
                    pitch_str = get_pitch_func(degree, octave)
                    p = pitch.Pitch(pitch_str)

                    # Verificar rango
                    if not (self.melodic_range[0] <= p.midi <= self.melodic_range[1]):
                        continue

                    candidate = NoteCandidate(
                        degree=degree,
                        octave=octave,
                        pitch_str=pitch_str,
                    )

                    # Calcular scores individuales
                    self._score_voice_leading(candidate, last_pitch)
                    self._score_harmonic(candidate, metric_strength)
                    self._score_contour(candidate, target_degree, phrase_position)
                    self._score_tendency(candidate, last_pitch)
                    self._score_variety(candidate)
                    self._score_range(candidate)

                    # Calcular total
                    candidate.calculate_total(self.weights)
                    candidates.append(candidate)

                except Exception:
                    continue

        # Ordenar por score (mejor primero)
        candidates.sort(key=lambda c: c.total_score, reverse=True)
        return candidates

    def _score_voice_leading(
        self, candidate: NoteCandidate, last_pitch: Optional[str]
    ):
        """Evalua conduccion de voces."""
        if not last_pitch:
            candidate.voice_leading_score = 0.8  # Neutral para primera nota
            return

        last_p = pitch.Pitch(last_pitch)
        current_p = pitch.Pitch(candidate.pitch_str)

        intv = abs(int(current_p.ps - last_p.ps))

        # Scoring basado en tamano del intervalo
        # Preferir grados conjuntos (1-2 semitonos)
        if intv == 0:
            score = 0.6  # Unisono: aceptable pero no ideal
        elif intv <= 2:
            score = 1.0  # Segunda: ideal
        elif intv <= 4:
            score = 0.85  # Tercera: muy bueno
        elif intv <= 5:
            score = 0.7  # Cuarta: bueno
        elif intv <= 7:
            score = 0.5  # Quinta: aceptable
        elif intv <= 9:
            score = 0.3  # Sexta: usar con cuidado
        else:
            score = 0.1  # Septima+: evitar

        candidate.voice_leading_score = score

    def _score_harmonic(
        self, candidate: NoteCandidate, metric_strength: MetricStrength
    ):
        """Evalua compatibilidad armonica."""
        is_chord_tone = candidate.degree in self.chord_tones

        if metric_strength == MetricStrength.STRONG:
            # Tiempo fuerte: preferir notas del acorde
            candidate.harmonic_score = 1.0 if is_chord_tone else 0.3
        elif metric_strength == MetricStrength.SEMI_STRONG:
            candidate.harmonic_score = 0.9 if is_chord_tone else 0.5
        else:
            # Tiempo debil: notas de paso aceptables
            candidate.harmonic_score = 0.8 if is_chord_tone else 0.7

    def _score_contour(
        self,
        candidate: NoteCandidate,
        target_degree: Optional[int],
        phrase_position: PhrasePosition,
    ):
        """Evalua adherencia al contorno planificado."""
        if target_degree is None:
            candidate.contour_score = 0.5  # Neutral
            return

        # Distancia al grado objetivo
        distance = abs(candidate.degree - target_degree)

        # Penalizar mas en posiciones criticas
        if phrase_position in [PhrasePosition.CLIMAX, PhrasePosition.FINAL]:
            # En climax/final, queremos exactitud
            if distance == 0:
                score = 1.0
            elif distance == 1:
                score = 0.6
            else:
                score = 0.2
        else:
            # En otras posiciones, mas flexibilidad
            score = max(0.3, 1.0 - (distance * 0.15))

        candidate.contour_score = score

    def _score_tendency(
        self, candidate: NoteCandidate, last_pitch: Optional[str]
    ):
        """Evalua resolucion de notas de tendencia."""
        if not last_pitch:
            candidate.tendency_score = 0.7
            return

        # Obtener grado anterior (aproximado)
        # TODO: Esto deberia venir del contexto
        last_degree = self.recent_degrees[-1] if self.recent_degrees else None

        if last_degree in self.tendency_tones:
            expected_resolution = self.tendency_tones[last_degree]
            if candidate.degree == expected_resolution:
                candidate.tendency_score = 1.0  # Resolucion correcta
            else:
                candidate.tendency_score = 0.3  # No resuelve
        else:
            candidate.tendency_score = 0.7  # No habia nota de tendencia

    def _score_variety(self, candidate: NoteCandidate):
        """Evalua variedad melodica (evitar repeticion excesiva)."""
        if not self.recent_degrees:
            candidate.variety_score = 0.8
            return

        # Contar ocurrencias recientes del grado
        count = self.recent_degrees.count(candidate.degree)

        if count == 0:
            score = 1.0  # Grado fresco
        elif count == 1:
            score = 0.8
        elif count == 2:
            score = 0.5
        else:
            score = 0.2  # Demasiada repeticion

        candidate.variety_score = score

    def _score_range(self, candidate: NoteCandidate):
        """Evalua posicion dentro del rango (preferir centro)."""
        p = pitch.Pitch(candidate.pitch_str)
        midi = p.midi

        range_min, range_max = self.melodic_range
        range_center = (range_min + range_max) / 2
        range_span = range_max - range_min

        # Distancia al centro normalizada
        distance_from_center = abs(midi - range_center) / (range_span / 2)

        # Preferir centro del rango
        candidate.range_score = max(0.2, 1.0 - (distance_from_center * 0.5))

    def add_markov_scores(
        self,
        candidates: List[NoteCandidate],
        markov_probabilities: Dict[int, float],  # {degree: probability}
    ):
        """
        Anade scores de Markov a los candidatos.

        Args:
            candidates: Lista de candidatos a actualizar
            markov_probabilities: Probabilidades de Markov por grado
        """
        if not markov_probabilities:
            for c in candidates:
                c.markov_score = 0.5  # Neutral
            return

        max_prob = max(markov_probabilities.values()) if markov_probabilities else 1.0

        for candidate in candidates:
            prob = markov_probabilities.get(candidate.degree, 0.0)
            # Normalizar a 0-1
            candidate.markov_score = prob / max_prob if max_prob > 0 else 0.5

    def select_best(
        self,
        candidates: List[NoteCandidate],
        temperature: float = 0.3,
    ) -> NoteCandidate:
        """
        Selecciona el mejor candidato con algo de aleatoriedad controlada.

        Args:
            candidates: Candidatos ordenados por score
            temperature: 0.0 = siempre el mejor, 1.0 = muy aleatorio

        Returns:
            Candidato seleccionado
        """
        if not candidates:
            raise ValueError("No candidates available")

        if temperature == 0.0 or len(candidates) == 1:
            return candidates[0]

        # Tomar los mejores candidatos
        top_n = min(5, len(candidates))
        top_candidates = candidates[:top_n]

        # Convertir scores a pesos para seleccion
        scores = [c.total_score for c in top_candidates]
        min_score = min(scores)

        # Ajustar por temperatura
        adjusted_scores = [
            (s - min_score + 0.01) ** (1.0 / (temperature + 0.1))
            for s in scores
        ]

        total = sum(adjusted_scores)
        weights = [s / total for s in adjusted_scores]

        return random.choices(top_candidates, weights=weights)[0]

    def update_history(self, degree: int):
        """Actualiza historial para calculo de variedad."""
        self.recent_degrees.append(degree)
        if len(self.recent_degrees) > self.max_history:
            self.recent_degrees.pop(0)

    def reset(self):
        """Reinicia el historial."""
        self.recent_degrees = []
