"""
Clases base para cadenas de Markov musicales.
Contiene MarkovChain genérica y BaseMarkovModel abstracta.
"""

import ast
import json
import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Constantes para filtrado diatónico
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


# ============================================================================
# Funciones auxiliares para filtrado diatónico
# ============================================================================

def get_diatonic_pitch_classes(key_name: str, mode: str = "major") -> set:
    """
    Obtiene las pitch classes diatónicas para una tonalidad.

    Args:
        key_name: Nombre de la tónica (ej: "C", "D", "Eb")
        mode: "major", "minor", o modos griegos

    Returns:
        Set de pitch classes diatónicas (0-11)
    """
    tonic_pc = TONIC_TO_PITCH_CLASS.get(key_name, 0)

    if mode in ("minor", "aeolian", "natural_minor"):
        base_pcs = MINOR_SCALE_PITCH_CLASSES
    else:
        base_pcs = MAJOR_SCALE_PITCH_CLASSES

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


# ============================================================================
# Clase MarkovChain genérica
# ============================================================================

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
            return

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
            temperature: Control de aleatoriedad (1.0 = distribución original)

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

        states = list(next_states.keys())
        counts = list(next_states.values())

        if temperature != 1.0:
            total = sum(counts)
            probs = [c / total for c in counts]
            probs = [p ** (1.0 / temperature) for p in probs]
            total_prob = sum(probs)
            weights = [p / total_prob for p in probs]
        else:
            weights = counts

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
        """Guarda modelo entrenado a JSON."""
        json_transitions = {}

        for state_key, next_states in self.transitions.items():
            serializable_next = {}
            for next_state, count in next_states.items():
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
        """Carga modelo entrenado desde JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.order = data["order"]
        self.total_transitions = data["total_transitions"]

        self.transitions = {}

        for state_key, next_states in data["transitions"].items():
            reconstructed_next = {}

            for next_key, count in next_states.items():
                try:
                    next_state = ast.literal_eval(next_key)
                except (ValueError, SyntaxError, TypeError):
                    next_state = next_key

                reconstructed_next[next_state] = count

            self.transitions[state_key] = reconstructed_next


# ============================================================================
# Clase base abstracta para modelos musicales
# ============================================================================

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
        """Actualiza el historial con un nuevo valor."""
        self._history.append(value)
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
