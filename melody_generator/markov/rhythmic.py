"""
Modelo de Markov para patrones rítmicos.
Contiene RhythmicMarkovModel.
"""

import random
from fractions import Fraction
from math import gcd
from typing import Any, List, Optional, Tuple

from .base import BaseMarkovModel


class RhythmicMarkovModel(BaseMarkovModel):
    """
    Modelo de Markov para patrones rítmicos.

    Estado = duración en forma (numerador, denominador)
    Ejemplo: (1, 4) = negra, (1, 8) = corchea
    """

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo rítmico.

        Args:
            order: Orden de la cadena (2 recomendado)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        super().__init__(order=order, composer=composer)
        self._rhythm_history = self._history

    def _quarter_length_to_tuple(self, ql: float) -> Tuple[int, int]:
        """
        Convierte quarterLength a tupla (num, denom).

        Ejemplos:
            1.0 → (1, 4)  # negra
            0.5 → (1, 8)  # corchea
            2.0 → (1, 2)  # blanca
            1.5 → (3, 8)  # negra con puntillo
            0.25 → (1, 16)  # semicorchea
        """
        frac = Fraction(ql).limit_denominator(32)

        numerator = frac.numerator
        denominator = 4 * frac.denominator

        g = gcd(numerator, denominator)
        numerator //= g
        denominator //= g

        return (numerator, denominator)

    def train_from_corpus(
        self,
        composer: str = "bach",
        max_works: Optional[int] = None,
        voice_part: int = 0,
    ):
        """
        Entrena desde corpus de music21.

        Args:
            composer: "bach", "mozart", "beethoven", "all"
            max_works: Límite de obras (None = todas)
            voice_part: Índice de voz a extraer (0 = soprano)
        """
        from music21 import corpus

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
        print(f"  Extrayendo patrones rítmicos...")

        all_durations = []
        works_processed = 0
        works_failed = 0

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

                durations = []
                for note in notes:
                    ql = note.quarterLength

                    if 0.0625 <= ql <= 4.0:
                        duration_tuple = self._quarter_length_to_tuple(ql)
                        durations.append(duration_tuple)

                if durations:
                    all_durations.extend(durations)
                    works_processed += 1

                if (idx + 1) % 50 == 0:
                    print(f"    Procesadas {idx + 1}/{len(results)} obras...")

            except Exception:
                works_failed += 1
                continue

        print(f"  Obras procesadas exitosamente: {works_processed}")
        print(f"  Obras omitidas (errores): {works_failed}")
        print(f"  Total de duraciones extraídas: {len(all_durations)}")

        print(f"  Entrenando cadena de Markov (orden {self.order})...")
        self.chain.train(all_durations)
        print(f"  Transiciones únicas aprendidas: {len(self.chain.transitions)}")

    def suggest_next(
        self, weight: float = 0.5, fallback: Optional[List[Any]] = None
    ) -> Tuple[int, int]:
        """
        Implementación de la interfaz abstracta.
        Delega a suggest_duration para compatibilidad.
        """
        return self.suggest_duration(weight=weight, fallback_durations=fallback)

    def suggest_duration(
        self,
        weight: float = 0.5,
        fallback_durations: Optional[List[Tuple[int, int]]] = None,
    ) -> Tuple[int, int]:
        """
        Sugiere siguiente duración basado en historial.

        Args:
            weight: Peso del Markov (0.0-1.0)
            fallback_durations: Opciones si Markov falla

        Returns:
            Tupla (numerador, denominador)
        """
        if fallback_durations is None:
            fallback_durations = [(1, 4), (1, 8)]

        prev_state = self._get_prev_state()
        if prev_state is None:
            return random.choice(fallback_durations)

        if random.random() > weight:
            return random.choice(fallback_durations)

        markov_suggestion = self.chain.predict_next(prev_state)

        if markov_suggestion is None:
            return random.choice(fallback_durations)

        return markov_suggestion
