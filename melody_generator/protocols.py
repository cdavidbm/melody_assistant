"""
Protocolos e interfaces para el generador de melodías.
Define contratos que permiten inyección de dependencias y testing.
"""

from typing import List, Optional, Protocol, Tuple, Any

from .models import (
    HarmonicFunction,
    NoteFunction,
    RhythmicPattern,
    MelodicContour,
    Motif,
)


class ScaleManagerProtocol(Protocol):
    """Protocolo para gestión de escalas y modos."""

    def get_pitch_by_degree(
        self, degree: int, octave: int = 4
    ) -> str:
        """Obtiene el pitch para un grado de la escala."""
        ...

    def pitch_to_degree(self, pitch_str: str) -> int:
        """Convierte un pitch a su grado en la escala."""
        ...

    def is_chord_tone(self, degree: int, chord_tones: List[int]) -> bool:
        """Verifica si un grado es nota del acorde."""
        ...

    def is_in_range(self, pitch) -> bool:
        """Verifica si un pitch está dentro del rango melódico."""
        ...


class HarmonyManagerProtocol(Protocol):
    """Protocolo para gestión armónica."""

    def get_harmonic_function(
        self, measure_index: int, beat_index: int
    ) -> HarmonicFunction:
        """Obtiene la función armónica para una posición."""
        ...

    def get_chord_tones_for_function(
        self, harmonic_function: HarmonicFunction
    ) -> List[int]:
        """Obtiene las notas del acorde para una función armónica."""
        ...

    def create_harmonic_progression(
        self, num_measures: int
    ) -> List[HarmonicFunction]:
        """Crea una progresión armónica."""
        ...


class RhythmGeneratorProtocol(Protocol):
    """Protocolo para generación rítmica."""

    strong_beats: List[int]
    base_rhythmic_motif: Optional[RhythmicPattern]

    def create_rhythmic_pattern(self, num_beats: int) -> RhythmicPattern:
        """Crea un patrón rítmico."""
        ...

    def get_rhythmic_pattern_with_variation(
        self, measure_index: int
    ) -> RhythmicPattern:
        """Obtiene patrón rítmico con variación."""
        ...

    def initialize_base_motif(self) -> None:
        """Inicializa el motivo rítmico base."""
        ...


class PitchSelectorProtocol(Protocol):
    """Protocolo para selección de tonos."""

    def select_melodic_pitch(
        self,
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        rhythm_pattern: RhythmicPattern,
        note_index_in_measure: int,
    ) -> Tuple[str, NoteFunction]:
        """Selecciona el tono melódico."""
        ...

    def should_use_rest(
        self,
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        is_phrase_boundary: bool,
    ) -> bool:
        """Determina si usar silencio."""
        ...

    def set_last_was_rest(self, value: bool) -> None:
        """Actualiza estado de silencio previo."""
        ...


class MotifGeneratorProtocol(Protocol):
    """Protocolo para generación de motivos."""

    def create_base_motif(self, starting_degree: int = 1) -> Motif:
        """Crea el motivo base."""
        ...

    def apply_motif_variation(
        self, motif: Motif, variation_type: str = "auto"
    ) -> Motif:
        """Aplica variación a un motivo."""
        ...


class LilyPondFormatterProtocol(Protocol):
    """Protocolo para formateo LilyPond."""

    meter_tuple: Tuple[int, int]

    def convert_to_abjad_pitch(self, pitch_str: str) -> str:
        """Convierte pitch a formato Abjad."""
        ...

    def format_output(
        self,
        staff,  # abjad.Staff
        title: Optional[str] = None,
        composer: Optional[str] = None,
    ) -> str:
        """Formatea la salida LilyPond."""
        ...

    def create_key_signature(self):
        """Crea la armadura de clave."""
        ...


class MarkovModelProtocol(Protocol):
    """Protocolo base para modelos de Markov."""

    order: int
    composer: str

    def update_history(self, value: Any) -> None:
        """Actualiza el historial con un valor."""
        ...

    def reset_history(self) -> None:
        """Reinicia el historial."""
        ...


class MelodicMarkovProtocol(MarkovModelProtocol, Protocol):
    """Protocolo para modelo de Markov melódico."""

    def suggest_interval(
        self, weight: float = 0.5, fallback_intervals: Optional[List[int]] = None
    ) -> int:
        """Sugiere un intervalo melódico."""
        ...


class RhythmicMarkovProtocol(MarkovModelProtocol, Protocol):
    """Protocolo para modelo de Markov rítmico."""

    def suggest_duration(
        self,
        weight: float = 0.5,
        fallback_durations: Optional[List[Tuple[int, int]]] = None,
    ) -> Tuple[int, int]:
        """Sugiere una duración rítmica."""
        ...


class PeriodGeneratorProtocol(Protocol):
    """Protocolo para generación de períodos."""

    def generate_period(self):  # -> abjad.Staff
        """Genera un período musical (método tradicional)."""
        ...

    def generate_period_hierarchical(
        self, return_structure: bool = False
    ):  # -> abjad.Staff | Tuple[abjad.Staff, Period]
        """Genera un período con estructura jerárquica."""
        ...
