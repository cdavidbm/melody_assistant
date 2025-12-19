"""
Modelos de Markov para patrones melódicos.
Contiene MelodicMarkovModel y EnhancedMelodicMarkovModel.
"""

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseMarkovModel, MAJOR_SCALE_PITCH_CLASSES

logger = logging.getLogger(__name__)


class MelodicMarkovModel(BaseMarkovModel):
    """
    Modelo de Markov específico para intervalos melódicos.

    Estado = intervalo en semitonos (-12 a +12)
    Aprende patrones de transición de compositores clásicos.
    """

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo melódico.

        Args:
            order: Orden de la cadena (2 o 3 recomendado)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        super().__init__(order=order, composer=composer)
        self._interval_history = self._history

    def train_from_corpus(
        self,
        composer: str = "bach",
        max_works: Optional[int] = None,
        voice_part: int = 0,
        diatonic_only: bool = True,
    ):
        """
        Entrena desde el corpus de music21.

        Args:
            composer: "bach", "mozart", "beethoven", "all"
            max_works: Límite de obras (None = todas)
            voice_part: Índice de voz a extraer (0 = soprano/voz superior)
            diatonic_only: Si True, solo entrena con intervalos diatónicos
        """
        from music21 import corpus, interval

        print(f"  Buscando obras de {composer}...")

        if composer.lower() == "all":
            results = []
            for comp in ["bach", "mozart", "beethoven"]:
                results.extend(corpus.search(comp, field="composer"))
        else:
            results = corpus.search(composer, field="composer")

        if max_works:
            results = results[:max_works]

        print(f"  Encontradas {len(results)} obras")
        filter_msg = " (solo diatónicos)" if diatonic_only else ""
        print(f"  Extrayendo intervalos melódicos{filter_msg}...")

        all_intervals = []
        works_processed = 0
        works_failed = 0
        intervals_filtered = 0

        for idx, work in enumerate(results):
            try:
                score = work.parse()

                if len(score.parts) > voice_part:
                    melody = score.parts[voice_part]
                else:
                    melody = score.flatten()

                notes = melody.flatten().notes.stream()

                if len(notes) < 2:
                    continue

                intervals = []
                for i in range(len(notes) - 1):
                    try:
                        intv = interval.Interval(
                            noteStart=notes[i], noteEnd=notes[i + 1]
                        )
                        semitones = int(intv.semitones)
                        if -12 <= semitones <= 12:
                            if diatonic_only:
                                pc1 = notes[i].pitch.midi % 12
                                pc2 = notes[i + 1].pitch.midi % 12
                                if (pc1 in MAJOR_SCALE_PITCH_CLASSES and
                                    pc2 in MAJOR_SCALE_PITCH_CLASSES):
                                    intervals.append(semitones)
                                else:
                                    intervals_filtered += 1
                            else:
                                intervals.append(semitones)
                    except Exception as e:
                        logger.debug(f"Error calculando intervalo: {e}")
                        continue

                if intervals:
                    all_intervals.extend(intervals)
                    works_processed += 1

                if (idx + 1) % 50 == 0:
                    print(f"    Procesadas {idx + 1}/{len(results)} obras...")

            except Exception:
                works_failed += 1
                continue

        print(f"  Obras procesadas exitosamente: {works_processed}")
        print(f"  Obras omitidas (errores): {works_failed}")
        print(f"  Total de intervalos extraídos: {len(all_intervals)}")
        if diatonic_only:
            print(f"  Intervalos cromáticos filtrados: {intervals_filtered}")

        print(f"  Entrenando cadena de Markov (orden {self.order})...")
        self.chain.train(all_intervals)
        print(f"  Transiciones únicas aprendidas: {len(self.chain.transitions)}")

    def suggest_next(
        self, weight: float = 0.5, fallback: Optional[List[Any]] = None
    ) -> int:
        """
        Implementación de la interfaz abstracta.
        Delega a suggest_interval para compatibilidad.
        """
        return self.suggest_interval(weight=weight, fallback_intervals=fallback)

    def suggest_interval(
        self, weight: float = 0.5, fallback_intervals: Optional[List[int]] = None
    ) -> int:
        """
        Sugiere siguiente intervalo basado en historial.

        Args:
            weight: Peso del Markov (0.0-1.0)
            fallback_intervals: Opciones si Markov falla

        Returns:
            Intervalo sugerido en semitonos
        """
        if fallback_intervals is None:
            fallback_intervals = [-1, 1, 2]

        prev_state = self._get_prev_state()
        if prev_state is None:
            return random.choice(fallback_intervals)

        if random.random() > weight:
            return random.choice(fallback_intervals)

        markov_suggestion = self.chain.predict_next(prev_state)

        if markov_suggestion is None:
            return random.choice(fallback_intervals)

        return markov_suggestion

    def get_probability(self, interval: int) -> float:
        """
        Obtiene la probabilidad de un intervalo específico dado el historial.
        """
        prev_state = self._get_prev_state()
        if prev_state is None:
            return 1.0 / 25

        return self.chain.get_probability(prev_state, interval)

    def get_all_probabilities(self) -> Dict[int, float]:
        """Obtiene probabilidades para todos los intervalos posibles."""
        prev_state = self._get_prev_state()
        probs = {}

        for interval in range(-12, 13):
            if prev_state is None:
                probs[interval] = 1.0 / 25
            else:
                probs[interval] = self.chain.get_probability(prev_state, interval)

        return probs


class EnhancedMelodicMarkovModel(BaseMarkovModel):
    """
    Modelo de Markov mejorado para melodías.

    Usa estado enriquecido que incluye:
    - Grado de la escala (1-7)
    - Contexto métrico (fuerte/débil)
    - Dirección melódica (ascendente/descendente/estacionario)
    """

    # Mapeo de pitch class a grado de escala mayor
    PITCH_CLASS_TO_DEGREE = {
        0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7,
    }

    DIATONIC_PITCH_CLASSES = {0, 2, 4, 5, 7, 9, 11}

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo mejorado.

        Args:
            order: Orden de la cadena (2 recomendado)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        super().__init__(order=order, composer=composer)
        self._degree_history: List[int] = []
        self._metric_history: List[str] = []
        self._direction_history: List[int] = []

    def _make_state(
        self, degree: int, metric: str, direction: int
    ) -> Tuple[int, str, int]:
        """Crea una tupla de estado."""
        return (degree, metric, direction)

    def _extract_melody_features(
        self, notes, beats_per_measure: int = 4
    ) -> List[Tuple[int, str, int]]:
        """
        Extrae características melódicas de una secuencia de notas.
        Solo extrae notas diatónicas para evitar atonalidad.
        """
        features = []
        prev_midi = None

        for note in notes:
            try:
                if hasattr(note, 'pitch'):
                    midi = note.pitch.midi
                    pitch_class = midi % 12

                    if pitch_class not in self.DIATONIC_PITCH_CLASSES:
                        continue

                    degree = self.PITCH_CLASS_TO_DEGREE.get(pitch_class)
                    if degree is None:
                        continue

                    beat = note.beat if hasattr(note, 'beat') else 1
                    metric = "strong" if beat in [1, 3] else "weak"

                    if prev_midi is None:
                        direction = 0
                    elif midi > prev_midi:
                        direction = 1
                    elif midi < prev_midi:
                        direction = -1
                    else:
                        direction = 0

                    features.append((degree, metric, direction))
                    prev_midi = midi
            except Exception:
                continue

        return features

    def train_from_corpus(
        self,
        composer: str = "bach",
        max_works: Optional[int] = None,
        voice_part: int = 0,
    ):
        """Entrena desde corpus de music21 extrayendo solo soprano."""
        from music21 import corpus

        print(f"  Buscando obras de {composer} (Enhanced Markov)...")

        if composer.lower() == "all":
            results = []
            for comp in ["bach", "mozart", "beethoven"]:
                results.extend(corpus.search(comp, field="composer"))
        else:
            results = corpus.search(composer, field="composer")

        if max_works:
            results = results[:max_works]

        print(f"  Encontradas {len(results)} obras")
        print(f"  Extrayendo características melódicas (grado+métrica+dirección)...")

        all_features = []
        works_processed = 0

        for idx, work in enumerate(results):
            try:
                score = work.parse()

                if len(score.parts) > voice_part:
                    melody = score.parts[voice_part]
                else:
                    continue

                notes = list(melody.flatten().notes.stream())

                if len(notes) < 3:
                    continue

                ts = melody.getTimeSignatures()[0] if melody.getTimeSignatures() else None
                beats_per_measure = ts.numerator if ts else 4

                features = self._extract_melody_features(notes, beats_per_measure)

                if len(features) >= self.order + 1:
                    all_features.extend(features)
                    works_processed += 1

                if (idx + 1) % 50 == 0:
                    print(f"    Procesadas {idx + 1}/{len(results)} obras...")

            except Exception:
                continue

        print(f"  Obras procesadas: {works_processed}")
        print(f"  Total de estados extraídos: {len(all_features)}")

        print(f"  Entrenando cadena de Markov (orden {self.order})...")
        self.chain.train(all_features)
        print(f"  Transiciones únicas: {len(self.chain.transitions)}")

    def suggest_next(
        self, weight: float = 0.5, fallback: Optional[List[Any]] = None
    ) -> Tuple[int, str, int]:
        """Sugiere siguiente estado (degree, metric, direction)."""
        return self.suggest_degree(weight=weight)

    def suggest_degree(
        self,
        current_metric: str = "weak",
        weight: float = 0.5,
        fallback_degrees: Optional[List[int]] = None,
    ) -> int:
        """
        Sugiere siguiente grado basado en contexto.

        Args:
            current_metric: Contexto métrico actual ("strong" | "weak")
            weight: Peso de Markov (0.0-1.0)
            fallback_degrees: Grados de respaldo si Markov falla

        Returns:
            Grado sugerido (1-7)
        """
        if fallback_degrees is None:
            fallback_degrees = [1, 3, 5]

        prev_state = self._get_prev_state()
        if prev_state is None:
            return random.choice(fallback_degrees)

        if random.random() > weight:
            return random.choice(fallback_degrees)

        suggestion = self.chain.predict_next(prev_state)

        if suggestion is None:
            return random.choice(fallback_degrees)

        if isinstance(suggestion, tuple) and len(suggestion) >= 1:
            return suggestion[0]
        return random.choice(fallback_degrees)

    def update_history(self, degree: int, metric: str = "weak", direction: int = 0):
        """Actualiza historial con nuevo estado."""
        state = (degree, metric, direction)
        self._history.append(state)

        max_history = self.order + 20
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]

    def get_degree_probabilities(
        self, current_metric: str = "weak"
    ) -> Dict[int, float]:
        """Obtiene probabilidades para cada grado dado el contexto."""
        prev_state = self._get_prev_state()
        probs = {}

        for degree in range(1, 8):
            for direction in [-1, 0, 1]:
                test_state = (degree, current_metric, direction)

                if prev_state is None:
                    prob = 1.0 / 21
                else:
                    prob = self.chain.get_probability(prev_state, test_state)

                probs[degree] = probs.get(degree, 0) + prob

        return probs
