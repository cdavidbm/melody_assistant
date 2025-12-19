"""
Modelos de Markov con contexto armónico.
Contiene HarmonicContextMarkovModel y CadenceMarkovModel.
"""

import random
from typing import Any, Dict, List, Optional, Tuple

from .base import BaseMarkovModel


class HarmonicContextMarkovModel(BaseMarkovModel):
    """
    Modelo de Markov con contexto armónico completo.

    Estado = (interval, harmonic_degree, beat_position)

    Este modelo aprende patrones como:
    "Sobre el acorde de V (grado 5), en tiempo fuerte,
     después de un intervalo ascendente, la melodía
     tiende a resolver por grado conjunto descendente"
    """

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo con contexto armónico.

        Args:
            order: Orden de la cadena (2 recomendado)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        super().__init__(order=order, composer=composer)
        self._current_harmony = 1

    def _make_state(
        self,
        interval: int,
        harmony: int,
        beat_strength: str,
    ) -> Tuple[int, int, str]:
        """Crea una tupla de estado enriquecido."""
        interval = max(-12, min(12, interval))
        harmony = max(1, min(7, harmony))
        return (interval, harmony, beat_strength)

    def train_from_corpus(
        self,
        composer: str = "bach",
        max_works: Optional[int] = None,
        voice_part: int = 0,
    ):
        """Entrena desde corpus extrayendo contexto armónico."""
        from music21 import corpus

        print(f"  Buscando obras de {composer} (Harmonic Context)...")

        if composer.lower() == "all":
            results = []
            for comp in ["bach", "mozart", "beethoven"]:
                results.extend(corpus.search(comp, field="composer"))
        else:
            results = corpus.search(composer, field="composer")

        if max_works:
            results = results[:max_works]

        print(f"  Encontradas {len(results)} obras")
        print(f"  Extrayendo intervalos con contexto armónico...")

        all_states = []
        works_processed = 0

        for idx, work in enumerate(results):
            try:
                score = work.parse()

                if len(score.parts) <= voice_part:
                    continue

                melody = score.parts[voice_part]
                notes = list(melody.flatten().notes.stream())

                if len(notes) < 3:
                    continue

                try:
                    key_result = score.analyze('key')
                    key_name = key_result.tonic.name if key_result else 'C'
                except Exception:
                    key_name = 'C'

                prev_midi = None
                for note in notes:
                    try:
                        if hasattr(note, 'pitch'):
                            midi = note.pitch.midi

                            if prev_midi is not None:
                                intv = midi - prev_midi
                                if -12 <= intv <= 12:
                                    pc = midi % 12
                                    degree_map = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
                                    harmony = degree_map.get(pc, 1)

                                    beat = note.beat if hasattr(note, 'beat') else 1
                                    beat_strength = "strong" if beat == 1 else "weak"

                                    state = self._make_state(intv, harmony, beat_strength)
                                    all_states.append(state)

                            prev_midi = midi
                    except Exception:
                        continue

                works_processed += 1

                if (idx + 1) % 50 == 0:
                    print(f"    Procesadas {idx + 1}/{len(results)} obras...")

            except Exception:
                continue

        print(f"  Obras procesadas: {works_processed}")
        print(f"  Estados extraídos: {len(all_states)}")

        print(f"  Entrenando cadena de Markov (orden {self.order})...")
        self.chain.train(all_states)
        print(f"  Transiciones únicas: {len(self.chain.transitions)}")

    def set_current_harmony(self, harmony: int):
        """Establece el contexto armónico actual."""
        self._current_harmony = max(1, min(7, harmony))

    def suggest_next(
        self,
        weight: float = 0.5,
        fallback: Optional[List[Any]] = None,
    ) -> int:
        """Sugiere siguiente intervalo."""
        return self.suggest_interval(
            harmony=self._current_harmony,
            beat_strength="weak",
            weight=weight,
            fallback_intervals=fallback,
        )

    def suggest_interval(
        self,
        harmony: int,
        beat_strength: str = "weak",
        weight: float = 0.5,
        fallback_intervals: Optional[List[int]] = None,
    ) -> int:
        """Sugiere intervalo considerando contexto armónico."""
        if fallback_intervals is None:
            fallback_intervals = [-2, -1, 1, 2]

        prev_state = self._get_prev_state()
        if prev_state is None:
            return random.choice(fallback_intervals)

        if random.random() > weight:
            return random.choice(fallback_intervals)

        suggestion = self.chain.predict_next(prev_state)

        if suggestion is None:
            return random.choice(fallback_intervals)

        if isinstance(suggestion, tuple) and len(suggestion) >= 1:
            return suggestion[0]
        return random.choice(fallback_intervals)

    def update_history(
        self,
        interval: int,
        harmony: int = 1,
        beat_strength: str = "weak",
    ):
        """Actualiza historial con nuevo estado."""
        state = self._make_state(interval, harmony, beat_strength)
        self._history.append(state)

        max_history = self.order + 20
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]

    def get_interval_probabilities_for_harmony(
        self,
        harmony: int,
        beat_strength: str = "weak",
    ) -> Dict[int, float]:
        """Obtiene probabilidades de intervalos para un contexto armónico."""
        prev_state = self._get_prev_state()
        probs = {}

        for interval in range(-12, 13):
            test_state = self._make_state(interval, harmony, beat_strength)

            if prev_state is None:
                prob = 1.0 / 25
            else:
                prob = self.chain.get_probability(prev_state, test_state)

            probs[interval] = prob

        return probs


class CadenceMarkovModel(BaseMarkovModel):
    """
    Modelo de Markov especializado en patrones cadenciales.

    Aprende las fórmulas melódicas típicas que aparecen
    en cadencias (PAC, HC, DC, etc.) de diferentes compositores.
    """

    CADENCE_PATTERNS = {
        "authentic": [[7, 1], [2, 1], [4, 3, 2, 1]],
        "half": [[1, 2], [3, 2], [5, 4, 3, 2]],
        "deceptive": [[7, 1], [2, 3]],
        "plagal": [[4, 3], [6, 5, 1]],
    }

    def __init__(self, order: int = 2, composer: str = "bach"):
        super().__init__(order=order, composer=composer)
        self._cadence_type = "authentic"

    def train_from_corpus(
        self,
        composer: str = "bach",
        max_works: Optional[int] = None,
        voice_part: int = 0,
    ):
        """Entrena desde corpus focalizándose en patrones cadenciales."""
        from music21 import corpus

        print(f"  Entrenando patrones cadenciales de {composer}...")

        if composer.lower() == "all":
            results = []
            for comp in ["bach", "mozart", "beethoven"]:
                results.extend(corpus.search(comp, field="composer"))
        else:
            results = corpus.search(composer, field="composer")

        if max_works:
            results = results[:max_works]

        all_patterns = []
        works_processed = 0

        for idx, work in enumerate(results):
            try:
                score = work.parse()

                if len(score.parts) <= voice_part:
                    continue

                melody = score.parts[voice_part]
                notes = list(melody.flatten().notes.stream())

                if len(notes) < 4:
                    continue

                for i in range(len(notes) - 3):
                    try:
                        if notes[i].quarterLength >= 1.0:
                            pattern = []
                            for j in range(max(0, i-2), i+2):
                                if j < len(notes) and hasattr(notes[j], 'pitch'):
                                    midi = notes[j].pitch.midi
                                    degree = ((midi % 12) // 2) % 7 + 1
                                    pattern.append(degree)

                            if len(pattern) >= 2:
                                all_patterns.append(tuple(pattern))
                    except Exception:
                        continue

                works_processed += 1

            except Exception:
                continue

        print(f"  Obras procesadas: {works_processed}")
        print(f"  Patrones cadenciales: {len(all_patterns)}")

        self.chain.train(all_patterns)
        print(f"  Transiciones únicas: {len(self.chain.transitions)}")

    def suggest_next(
        self,
        weight: float = 0.5,
        fallback: Optional[List[Any]] = None,
    ) -> int:
        """Sugiere siguiente grado en contexto cadencial."""
        return self.suggest_cadential_degree(weight=weight)

    def set_cadence_type(self, cadence_type: str):
        """Establece el tipo de cadencia esperada."""
        if cadence_type in self.CADENCE_PATTERNS:
            self._cadence_type = cadence_type

    def suggest_cadential_degree(
        self,
        weight: float = 0.5,
        fallback_degrees: Optional[List[int]] = None,
    ) -> int:
        """Sugiere siguiente grado para patrón cadencial."""
        if fallback_degrees is None:
            patterns = self.CADENCE_PATTERNS.get(self._cadence_type, [[2, 1]])
            fallback_degrees = patterns[0]

        prev_state = self._get_prev_state()
        if prev_state is None:
            return fallback_degrees[-1] if fallback_degrees else 1

        if random.random() > weight:
            idx = min(len(self._history), len(fallback_degrees) - 1)
            return fallback_degrees[idx] if idx >= 0 else 1

        suggestion = self.chain.predict_next(prev_state)

        if suggestion is None:
            return fallback_degrees[-1] if fallback_degrees else 1

        if isinstance(suggestion, tuple) and len(suggestion) > 0:
            return suggestion[-1]
        return fallback_degrees[-1] if fallback_degrees else 1

    def get_typical_patterns(self, cadence_type: str = None) -> List[List[int]]:
        """Obtiene patrones típicos para un tipo de cadencia."""
        ctype = cadence_type or self._cadence_type
        return self.CADENCE_PATTERNS.get(ctype, [[2, 1]])
