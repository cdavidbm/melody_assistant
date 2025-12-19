"""
Cadenas de Markov para generación musical.
Implementa aprendizaje de patrones melódicos y rítmicos desde corpus.
"""

import ast
import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from fractions import Fraction

logger = logging.getLogger(__name__)


# ============================================================================
# Constantes y funciones auxiliares para filtrado diatónico
# ============================================================================

# Pitch classes diatónicas para escala mayor (C=0)
MAJOR_SCALE_PITCH_CLASSES = {0, 2, 4, 5, 7, 9, 11}  # C, D, E, F, G, A, B

# Pitch classes diatónicas para escala menor natural (A=9)
MINOR_SCALE_PITCH_CLASSES = {0, 2, 3, 5, 7, 8, 10}  # A, B, C, D, E, F, G

# Mapeo de nombre de tónica a pitch class
TONIC_TO_PITCH_CLASS = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}


def get_diatonic_pitch_classes(key_name: str, mode: str = "major") -> set:
    """
    Obtiene las pitch classes diatónicas para una tonalidad.

    Args:
        key_name: Nombre de la tónica (ej: "C", "D", "Eb")
        mode: "major", "minor", o modos griegos

    Returns:
        Set de pitch classes diatónicas (0-11)
    """
    # Obtener pitch class de la tónica
    tonic_pc = TONIC_TO_PITCH_CLASS.get(key_name, 0)

    # Elegir patrón de escala
    if mode in ("minor", "aeolian", "natural_minor"):
        base_pcs = MINOR_SCALE_PITCH_CLASSES
    else:
        # Major y la mayoría de modos usan escala mayor como base
        base_pcs = MAJOR_SCALE_PITCH_CLASSES

    # Transponer al tono correcto
    return {(pc + tonic_pc) % 12 for pc in base_pcs}


def is_diatonic_interval(
    from_midi: int,
    interval_semitones: int,
    diatonic_pcs: set
) -> bool:
    """
    Verifica si un intervalo desde una nota resulta en nota diatónica.

    Args:
        from_midi: Nota MIDI de origen
        interval_semitones: Intervalo en semitonos
        diatonic_pcs: Set de pitch classes diatónicas

    Returns:
        True si la nota resultante es diatónica
    """
    target_midi = from_midi + interval_semitones
    target_pc = target_midi % 12
    return target_pc in diatonic_pcs


def filter_diatonic_intervals(
    from_midi: int,
    intervals: list,
    diatonic_pcs: set
) -> list:
    """
    Filtra una lista de intervalos para quedarse solo con los diatónicos.

    Args:
        from_midi: Nota MIDI de origen
        intervals: Lista de intervalos en semitonos
        diatonic_pcs: Set de pitch classes diatónicas

    Returns:
        Lista filtrada de intervalos diatónicos
    """
    return [
        intv for intv in intervals
        if is_diatonic_interval(from_midi, intv, diatonic_pcs)
    ]


class MarkovChain:
    """
    Cadena de Markov genérica de orden N.

    Soporta orden 1, 2, o 3 (contexto de 1-3 estados previos).
    Permite entrenamiento, predicción, y persistencia en JSON.
    """

    def __init__(self, order: int = 2):
        """
        Inicializa la cadena de Markov.

        Args:
            order: Orden de la cadena (1-3)
                   1 = solo estado previo
                   2 = dos estados previos (recomendado)
                   3 = tres estados previos (máximo contexto)
        """
        if order < 1 or order > 3:
            raise ValueError("Order must be between 1 and 3")

        self.order = order
        self.transitions: Dict[str, Dict[Any, int]] = {}
        self.total_transitions = 0

    def _state_to_key(self, state: Tuple) -> str:
        """Convierte tupla de estado a clave string para JSON."""
        return str(state)

    def _key_to_state(self, key: str) -> Tuple:
        """Convierte clave string de JSON a tupla de estado."""
        # Usar ast.literal_eval() en lugar de eval() por seguridad
        # Solo evalúa literales Python (tuplas, números, strings), no código arbitrario
        return ast.literal_eval(key)

    def add_transition(self, prev_state: Tuple, next_state: Any):
        """
        Registra una transición observada.

        Args:
            prev_state: Tupla de estados previos (longitud = self.order)
            next_state: Estado siguiente observado
        """
        if len(prev_state) != self.order:
            raise ValueError(f"prev_state must have length {self.order}")

        key = self._state_to_key(prev_state)

        if key not in self.transitions:
            self.transitions[key] = {}

        if next_state not in self.transitions[key]:
            self.transitions[key][next_state] = 0

        self.transitions[key][next_state] += 1
        self.total_transitions += 1

    def train(self, sequence: List[Any]):
        """
        Entrena la cadena con una secuencia completa.

        Args:
            sequence: Lista de estados observados
        """
        if len(sequence) < self.order + 1:
            return  # Secuencia muy corta

        for i in range(len(sequence) - self.order):
            prev_state = tuple(sequence[i : i + self.order])
            next_state = sequence[i + self.order]
            self.add_transition(prev_state, next_state)

    def predict_next(
        self, prev_state: Tuple, temperature: float = 1.0
    ) -> Optional[Any]:
        """
        Predice siguiente estado basado en contexto previo.

        Args:
            prev_state: Tupla de estados previos
            temperature: Control de aleatoriedad
                        1.0 = distribución original
                        <1.0 = más conservador (favorece alta probabilidad)
                        >1.0 = más aleatorio

        Returns:
            Siguiente estado predicho, o None si no hay datos
        """
        if len(prev_state) != self.order:
            return None

        key = self._state_to_key(prev_state)

        if key not in self.transitions:
            return None

        next_states = self.transitions[key]

        if not next_states:
            return None

        # Obtener estados y conteos
        states = list(next_states.keys())
        counts = list(next_states.values())

        # Aplicar temperature
        if temperature != 1.0:
            # Convertir a probabilidades
            total = sum(counts)
            probs = [c / total for c in counts]

            # Aplicar temperatura
            probs = [p ** (1.0 / temperature) for p in probs]

            # Re-normalizar
            total_prob = sum(probs)
            weights = [p / total_prob for p in probs]
        else:
            weights = counts

        # Selección ponderada
        return random.choices(states, weights=weights)[0]

    def get_probability(self, prev_state: Tuple, next_state: Any) -> float:
        """
        Obtiene probabilidad de transición específica.

        Returns:
            Probabilidad entre 0.0 y 1.0, o 0.0 si no existe
        """
        if len(prev_state) != self.order:
            return 0.0

        key = self._state_to_key(prev_state)

        if key not in self.transitions:
            return 0.0

        next_states = self.transitions[key]

        if next_state not in next_states:
            return 0.0

        total = sum(next_states.values())
        return next_states[next_state] / total

    def save(self, filepath: str):
        """
        Guarda modelo entrenado a JSON.

        Args:
            filepath: Ruta del archivo JSON de salida
        """
        # Convertir transiciones a formato JSON-serializable
        json_transitions = {}

        for state_key, next_states in self.transitions.items():
            # Convertir next_states values a formato serializable
            serializable_next = {}
            for next_state, count in next_states.items():
                # Convertir tuplas a strings para JSON
                if isinstance(next_state, tuple):
                    next_key = str(next_state)
                else:
                    next_key = str(next_state)
                serializable_next[next_key] = count

            json_transitions[state_key] = serializable_next

        data = {
            "order": self.order,
            "total_transitions": self.total_transitions,
            "transitions": json_transitions,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, filepath: str):
        """
        Carga modelo entrenado desde JSON.

        Args:
            filepath: Ruta del archivo JSON de entrada
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.order = data["order"]
        self.total_transitions = data["total_transitions"]

        # Reconstruir transiciones
        self.transitions = {}

        for state_key, next_states in data["transitions"].items():
            reconstructed_next = {}

            for next_key, count in next_states.items():
                # Intentar reconstruir tipo original
                try:
                    # Usar ast.literal_eval() por seguridad (solo evalúa literales)
                    next_state = ast.literal_eval(next_key)
                except (ValueError, SyntaxError, TypeError):
                    # Si falla, dejar como string
                    next_state = next_key

                reconstructed_next[next_state] = count

            self.transitions[state_key] = reconstructed_next


class BaseMarkovModel(ABC):
    """
    Clase base abstracta para modelos de Markov musicales.

    Proporciona funcionalidad común para modelos melódicos y rítmicos,
    siguiendo el principio de Liskov Substitution (LSP).
    """

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo base.

        Args:
            order: Orden de la cadena (1-3)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        self.order = order
        self.composer = composer
        self.chain = MarkovChain(order=order)
        self._history: List[Any] = []

    @abstractmethod
    def train_from_corpus(
        self, composer: str = "bach", max_works: Optional[int] = None, voice_part: int = 0
    ) -> None:
        """
        Entrena el modelo desde el corpus de music21.

        Args:
            composer: Compositor o "all" para todos
            max_works: Límite de obras (None = todas)
            voice_part: Índice de voz a extraer
        """
        ...

    @abstractmethod
    def suggest_next(self, weight: float = 0.5, fallback: Optional[List[Any]] = None) -> Any:
        """
        Sugiere el siguiente valor basado en historial.

        Args:
            weight: Peso del Markov (0.0-1.0)
            fallback: Valores de respaldo si Markov falla

        Returns:
            Valor sugerido
        """
        ...

    def update_history(self, value: Any) -> None:
        """
        Actualiza el historial con un nuevo valor.

        Args:
            value: Valor a agregar al historial
        """
        self._history.append(value)
        # Mantener ventana razonable
        max_history = self.order + 20
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]

    def reset_history(self) -> None:
        """Reinicia el historial (al empezar nueva melodía)."""
        self._history = []

    def _get_prev_state(self) -> Optional[Tuple]:
        """Obtiene el estado previo para predicción."""
        if len(self._history) < self.order:
            return None
        return tuple(self._history[-self.order:])


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
        # Alias para compatibilidad
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

        # Buscar obras del compositor
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

                # Extraer voz especificada
                if len(score.parts) > voice_part:
                    melody = score.parts[voice_part]
                else:
                    # Si no hay suficientes voces, intentar flatten
                    melody = score.flatten()

                # Obtener solo notas (sin acordes, silencios)
                notes = melody.flatten().notes.stream()

                if len(notes) < 2:
                    continue

                # Calcular intervalos consecutivos
                intervals = []
                for i in range(len(notes) - 1):
                    try:
                        intv = interval.Interval(
                            noteStart=notes[i], noteEnd=notes[i + 1]
                        )
                        # Limitar intervalos a rango razonable (-12 a +12)
                        semitones = int(intv.semitones)
                        if -12 <= semitones <= 12:
                            # Filtrado diatónico opcional
                            if diatonic_only:
                                # Verificar que ambas notas sean diatónicas en C mayor
                                # (asumimos que la música tonal tiene patrones similares)
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

                # Progreso cada 50 obras
                if (idx + 1) % 50 == 0:
                    print(f"    Procesadas {idx + 1}/{len(results)} obras...")

            except Exception as e:
                works_failed += 1
                continue

        print(f"  Obras procesadas exitosamente: {works_processed}")
        print(f"  Obras omitidas (errores): {works_failed}")
        print(f"  Total de intervalos extraídos: {len(all_intervals)}")
        if diatonic_only:
            print(f"  Intervalos cromáticos filtrados: {intervals_filtered}")

        # Entrenar cadena de Markov
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
                   0.0 = ignorar Markov, usar fallback
                   1.0 = confiar totalmente en Markov
            fallback_intervals: Opciones si Markov falla

        Returns:
            Intervalo sugerido en semitonos
        """
        if fallback_intervals is None:
            fallback_intervals = [-1, 1, 2]  # Grados conjuntos por defecto

        # Si no hay suficiente contexto, usar fallback
        prev_state = self._get_prev_state()
        if prev_state is None:
            return random.choice(fallback_intervals)

        # Decidir si usar Markov basado en weight
        if random.random() > weight:
            return random.choice(fallback_intervals)

        # Pedir sugerencia a Markov
        markov_suggestion = self.chain.predict_next(prev_state)

        if markov_suggestion is None:
            # No hay datos para este contexto, usar fallback
            return random.choice(fallback_intervals)

        return markov_suggestion

    def get_probability(self, interval: int) -> float:
        """
        Obtiene la probabilidad de un intervalo específico dado el historial.

        Args:
            interval: Intervalo en semitonos (-12 a +12)

        Returns:
            Probabilidad entre 0.0 y 1.0
        """
        prev_state = self._get_prev_state()
        if prev_state is None:
            # Sin historial suficiente, distribución uniforme
            return 1.0 / 25  # 25 intervalos posibles (-12 a +12)

        return self.chain.get_probability(prev_state, interval)

    def get_all_probabilities(self) -> Dict[int, float]:
        """
        Obtiene probabilidades para todos los intervalos posibles.

        Returns:
            Diccionario {intervalo: probabilidad}
        """
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

    Esto permite aprender patrones como:
    "En tiempo fuerte, después de ascender del grado 5 al 6,
     la melodía tiende a ir al grado 5 o 7"
    """

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo mejorado.

        Args:
            order: Orden de la cadena (2 recomendado)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        super().__init__(order=order, composer=composer)

        # Estado actual: (degree, metric, direction)
        self._degree_history: List[int] = []
        self._metric_history: List[str] = []  # "strong" | "weak"
        self._direction_history: List[int] = []  # 1 | 0 | -1

    def _make_state(
        self, degree: int, metric: str, direction: int
    ) -> Tuple[int, str, int]:
        """Crea una tupla de estado."""
        return (degree, metric, direction)

    # Mapeo de pitch class a grado de escala mayor
    # Solo notas diatónicas en C mayor: C=1, D=2, E=3, F=4, G=5, A=6, B=7
    PITCH_CLASS_TO_DEGREE = {
        0: 1,   # C
        2: 2,   # D
        4: 3,   # E
        5: 4,   # F
        7: 5,   # G
        9: 6,   # A
        11: 7,  # B
    }

    # Pitch classes diatónicas en C mayor
    DIATONIC_PITCH_CLASSES = {0, 2, 4, 5, 7, 9, 11}

    def _extract_melody_features(
        self, notes, beats_per_measure: int = 4
    ) -> List[Tuple[int, str, int]]:
        """
        Extrae características melódicas de una secuencia de notas.

        Solo extrae notas diatónicas para evitar entrenar sobre
        pasajes cromáticos que causarían atonalidad.

        Args:
            notes: Lista de notas de music21
            beats_per_measure: Pulsos por compás para determinar tiempo fuerte

        Returns:
            Lista de tuplas (degree, metric, direction)
        """
        features = []
        prev_midi = None

        for note in notes:
            try:
                if hasattr(note, 'pitch'):
                    midi = note.pitch.midi
                    pitch_class = midi % 12

                    # Solo procesar notas diatónicas (evitar cromáticas)
                    if pitch_class not in self.DIATONIC_PITCH_CLASSES:
                        continue

                    # Mapeo correcto de pitch class a grado
                    degree = self.PITCH_CLASS_TO_DEGREE.get(pitch_class)
                    if degree is None:
                        continue

                    # Determinar contexto métrico
                    beat = note.beat if hasattr(note, 'beat') else 1
                    metric = "strong" if beat in [1, 3] else "weak"

                    # Determinar dirección
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
        """
        Entrena desde corpus de music21 extrayendo solo soprano.

        Args:
            composer: "bach", "mozart", "beethoven", "all"
            max_works: Límite de obras (None = todas)
            voice_part: Índice de voz a extraer (0 = soprano)
        """
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

                # Extraer solo la voz soprano/superior
                if len(score.parts) > voice_part:
                    melody = score.parts[voice_part]
                else:
                    continue  # Skip si no hay suficientes partes

                # Obtener notas
                notes = list(melody.flatten().notes.stream())

                if len(notes) < 3:
                    continue

                # Determinar beats por compás
                ts = melody.getTimeSignatures()[0] if melody.getTimeSignatures() else None
                beats_per_measure = ts.numerator if ts else 4

                # Extraer características
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

        # Entrenar cadena
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

        # Pedir sugerencia a Markov
        suggestion = self.chain.predict_next(prev_state)

        if suggestion is None:
            return random.choice(fallback_degrees)

        # Extraer solo el grado de la sugerencia
        if isinstance(suggestion, tuple) and len(suggestion) >= 1:
            return suggestion[0]
        return random.choice(fallback_degrees)

    def update_history(self, degree: int, metric: str = "weak", direction: int = 0):
        """
        Actualiza historial con nuevo estado.

        Args:
            degree: Grado actual (1-7)
            metric: Contexto métrico ("strong" | "weak")
            direction: Dirección melódica (1, 0, -1)
        """
        state = (degree, metric, direction)
        self._history.append(state)

        # Mantener historial limitado
        max_history = self.order + 20
        if len(self._history) > max_history:
            self._history = self._history[-max_history:]

    def get_degree_probabilities(
        self, current_metric: str = "weak"
    ) -> Dict[int, float]:
        """
        Obtiene probabilidades para cada grado dado el contexto.

        Returns:
            Diccionario {degree: probability}
        """
        prev_state = self._get_prev_state()
        probs = {}

        for degree in range(1, 8):
            # Crear posibles estados con este grado
            for direction in [-1, 0, 1]:
                test_state = (degree, current_metric, direction)

                if prev_state is None:
                    prob = 1.0 / 21  # 7 grados * 3 direcciones
                else:
                    prob = self.chain.get_probability(prev_state, test_state)

                # Acumular probabilidad para este grado
                probs[degree] = probs.get(degree, 0) + prob

        return probs


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
        # Alias para compatibilidad
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

        Args:
            ql: quarterLength de music21

        Returns:
            Tupla (numerador, denominador) en notación musical
        """
        # Convertir a fracción
        frac = Fraction(ql).limit_denominator(32)

        # ql=1.0 es negra (denominador 4)
        # ql=0.5 es corchea (denominador 8)
        # Fórmula: denominador_musical = 4 / ql

        numerator = frac.numerator
        denominator = 4 * frac.denominator

        # Simplificar si es posible
        from math import gcd

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

        # Buscar obras del compositor
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

                # Extraer duraciones
                durations = []
                for note in notes:
                    ql = note.quarterLength

                    # Filtrar duraciones muy extrañas (>4.0 = redonda o más)
                    if 0.0625 <= ql <= 4.0:  # De semicorchea a redonda
                        duration_tuple = self._quarter_length_to_tuple(ql)
                        durations.append(duration_tuple)

                if durations:
                    all_durations.extend(durations)
                    works_processed += 1

                # Progreso cada 50 obras
                if (idx + 1) % 50 == 0:
                    print(f"    Procesadas {idx + 1}/{len(results)} obras...")

            except Exception:
                works_failed += 1
                continue

        print(f"  Obras procesadas exitosamente: {works_processed}")
        print(f"  Obras omitidas (errores): {works_failed}")
        print(f"  Total de duraciones extraídas: {len(all_durations)}")

        # Entrenar cadena de Markov
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
            fallback_durations = [(1, 4), (1, 8)]  # Negra, corchea

        # Si no hay suficiente contexto, usar fallback
        prev_state = self._get_prev_state()
        if prev_state is None:
            return random.choice(fallback_durations)

        # Decidir si usar Markov basado en weight
        if random.random() > weight:
            return random.choice(fallback_durations)

        # Pedir sugerencia a Markov
        markov_suggestion = self.chain.predict_next(prev_state)

        if markov_suggestion is None:
            return random.choice(fallback_durations)

        return markov_suggestion


class HarmonicContextMarkovModel(BaseMarkovModel):
    """
    Modelo de Markov con contexto armónico completo.

    Estado = (interval, harmonic_degree, beat_position)

    Este modelo aprende patrones como:
    "Sobre el acorde de V (grado 5), en tiempo fuerte,
     después de un intervalo ascendente, la melodía
     tiende a resolver por grado conjunto descendente"

    Ideal para generar melodías que respeten la armonía.
    """

    def __init__(self, order: int = 2, composer: str = "bach"):
        """
        Inicializa el modelo con contexto armónico.

        Args:
            order: Orden de la cadena (2 recomendado)
            composer: "bach", "mozart", "beethoven", "combined"
        """
        super().__init__(order=order, composer=composer)
        self._current_harmony = 1  # Grado armónico actual (1-7)

    def _make_state(
        self,
        interval: int,
        harmony: int,
        beat_strength: str,
    ) -> Tuple[int, int, str]:
        """
        Crea una tupla de estado enriquecido.

        Args:
            interval: Intervalo en semitonos
            harmony: Grado armónico actual (1-7)
            beat_strength: "strong" o "weak"

        Returns:
            Tupla de estado
        """
        # Normalizar intervalo a rango razonable
        interval = max(-12, min(12, interval))
        # Normalizar grado armónico
        harmony = max(1, min(7, harmony))

        return (interval, harmony, beat_strength)

    def train_from_corpus(
        self,
        composer: str = "bach",
        max_works: Optional[int] = None,
        voice_part: int = 0,
    ):
        """
        Entrena desde corpus extrayendo contexto armónico.

        Args:
            composer: "bach", "mozart", "beethoven", "all"
            max_works: Límite de obras
            voice_part: Voz a extraer (0 = soprano)
        """
        from music21 import corpus, analysis, interval

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

                # Intentar análisis armónico
                try:
                    # Usar análisis de notas romanas si está disponible
                    key_result = score.analyze('key')
                    key_name = key_result.tonic.name if key_result else 'C'
                except Exception:
                    key_name = 'C'

                # Extraer estados
                prev_midi = None
                for note in notes:
                    try:
                        if hasattr(note, 'pitch'):
                            midi = note.pitch.midi

                            # Calcular intervalo
                            if prev_midi is not None:
                                intv = midi - prev_midi
                                if -12 <= intv <= 12:
                                    # Determinar grado armónico aproximado
                                    # Simplificación: usar posición en escala
                                    pc = midi % 12
                                    # Asumir escala mayor para simplicidad
                                    degree_map = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
                                    harmony = degree_map.get(pc, 1)

                                    # Determinar posición métrica
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

        # Entrenar cadena
        print(f"  Entrenando cadena de Markov (orden {self.order})...")
        self.chain.train(all_states)
        print(f"  Transiciones únicas: {len(self.chain.transitions)}")

    def set_current_harmony(self, harmony: int):
        """
        Establece el contexto armónico actual.

        Args:
            harmony: Grado armónico (1-7)
        """
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
        """
        Sugiere intervalo considerando contexto armónico.

        Args:
            harmony: Grado armónico actual (1-7)
            beat_strength: "strong" o "weak"
            weight: Peso de Markov (0.0-1.0)
            fallback_intervals: Intervalos de respaldo

        Returns:
            Intervalo sugerido en semitonos
        """
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

        # Extraer solo el intervalo de la sugerencia
        if isinstance(suggestion, tuple) and len(suggestion) >= 1:
            return suggestion[0]
        return random.choice(fallback_intervals)

    def update_history(
        self,
        interval: int,
        harmony: int = 1,
        beat_strength: str = "weak",
    ):
        """
        Actualiza historial con nuevo estado.

        Args:
            interval: Intervalo en semitonos
            harmony: Grado armónico
            beat_strength: Posición métrica
        """
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
        """
        Obtiene probabilidades de intervalos para un contexto armónico.

        Útil para el sistema de scoring.

        Args:
            harmony: Grado armónico (1-7)
            beat_strength: Posición métrica

        Returns:
            Dict {intervalo: probabilidad}
        """
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

    Estado = (degree_sequence, cadence_type)
    """

    CADENCE_PATTERNS = {
        "authentic": [[7, 1], [2, 1], [4, 3, 2, 1]],
        "half": [[1, 2], [3, 2], [5, 4, 3, 2]],
        "deceptive": [[7, 1], [2, 3]],  # Resolución inesperada
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
        """
        Entrena desde corpus focalizándose en patrones cadenciales.
        """
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

                # Extraer patrones de final de frase (heurística)
                # Buscar notas largas seguidas de pausas o notas en tiempo 1
                for i in range(len(notes) - 3):
                    try:
                        # Si hay una nota larga, podría ser cadencia
                        if notes[i].quarterLength >= 1.0:
                            # Extraer los últimos 3-4 grados
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

        # Entrenar
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
        """
        Sugiere siguiente grado para patrón cadencial.

        Args:
            weight: Peso de Markov
            fallback_degrees: Grados de respaldo

        Returns:
            Grado sugerido (1-7)
        """
        if fallback_degrees is None:
            # Usar patrón típico según tipo de cadencia
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
            return suggestion[-1]  # Último grado del patrón
        return fallback_degrees[-1] if fallback_degrees else 1

    def get_typical_patterns(self, cadence_type: str = None) -> List[List[int]]:
        """
        Obtiene patrones típicos para un tipo de cadencia.

        Args:
            cadence_type: Tipo de cadencia (None = actual)

        Returns:
            Lista de patrones de grados
        """
        ctype = cadence_type or self._cadence_type
        return self.CADENCE_PATTERNS.get(ctype, [[2, 1]])
