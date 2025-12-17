"""
Modelos de datos para el generador de melodías.
Contiene enums y dataclasses que definen las estructuras fundamentales.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple


class ImpulseType(Enum):
    """Tipo de impulso inicial del motivo."""
    TETIC = "tetic"  # Comienza en tiempo fuerte
    ANACROUSTIC = "anacroustic"  # Comienza antes del tiempo fuerte
    ACEPHALOUS = "acephalous"  # Comienza después del tiempo fuerte


class NoteFunction(Enum):
    """Función de una nota en la jerarquía tonal."""
    STRUCTURAL = "structural"  # Nota del acorde (I, III, V)
    PASSING = "passing"  # Nota de paso
    NEIGHBOR = "neighbor"  # Bordadura
    APPOGGIATURA = "appoggiatura"  # Apoyatura


class MotivicVariation(Enum):
    """Tipos de variación motívica según teoría musical clásica."""
    ORIGINAL = "original"  # Motivo original sin variación
    INVERSION = "inversion"  # Inversión interválica
    RETROGRADE = "retrograde"  # Retrogradación (backwards)
    RETROGRADE_INVERSION = "retrograde_inversion"  # Retrogradación + inversión
    AUGMENTATION = "augmentation"  # Aumentación rítmica (valores más largos)
    DIMINUTION = "diminution"  # Disminución rítmica (valores más cortos)
    TRANSPOSITION = "transposition"  # Transposición a otro grado
    SEQUENCE = "sequence"  # Secuencia (repetición transpuesta)


@dataclass
class RhythmicPattern:
    """Patrón rítmico para un motivo."""
    durations: List[Tuple[int, int]]  # Lista de (numerador, denominador)
    strong_beat_indices: List[int]  # Índices de pulsos fuertes


@dataclass
class Motif:
    """Representa un motivo melódico."""
    pitches: List[str]  # Lista de pitches (ej: ["c'4", "d'4", "e'4"])
    intervals: List[int]  # Intervalos en semitonos entre notas consecutivas
    rhythm: RhythmicPattern  # Patrón rítmico del motivo
    degrees: List[int]  # Grados de la escala


@dataclass
class MelodicContour:
    """Control del contorno melódico y clímax."""
    max_range: int = 12  # Rango máximo en semitonos
    climax_position: float = 0.75  # Posición del clímax (0.0-1.0)
    prefer_stepwise: float = 0.7  # Probabilidad de movimiento por grado conjunto
    climax_approach_range: int = 3  # Compases de aproximación al clímax
    climax_emphasis: float = 1.5  # Factor de énfasis del clímax (multiplicador de registro)


@dataclass
class HarmonicFunction:
    """Función armónica implícita para un compás o grupo de compases."""
    degree: int  # Grado del acorde (1=I, 4=IV, 5=V, etc.)
    quality: str  # "major", "minor", "diminished", "augmented"
    tension: float  # Nivel de tensión (0.0=reposo, 1.0=máxima tensión)
    chord_tones: List[int]  # Grados de la escala que forman el acorde


@dataclass
class Phrase:
    """
    Frase musical: motivo + respuesta/variación (típicamente 2 compases).

    La frase es la unidad mínima de sentido musical completo.
    Contiene dos motivos: el original y su variación/respuesta.
    """
    motif: Motif  # Motivo base (primer compás)
    variation: Motif  # Variación/respuesta del motivo (segundo compás)
    harmonic_progression: List[HarmonicFunction]  # Progresión armónica de la frase
    measure_range: Tuple[int, int]  # (inicio, fin) en índices de compases
    variation_type: str = "auto"  # Tipo de variación aplicada

    def get_motifs(self) -> List[Motif]:
        """Retorna los motivos de la frase en orden."""
        return [self.motif, self.variation]


@dataclass
class Semiphrase:
    """
    Semifrase: agrupación de frases (típicamente 4 compases).

    En el período clásico, la semifrase representa el antecedente o consecuente.
    Contiene típicamente 2 frases (4 compases).
    """
    phrases: List[Phrase]  # Lista de frases que componen la semifrase
    function: str  # "antecedent" o "consequent"
    cadence_type: str  # "half" (semicadencia) o "authentic" (cadencia auténtica)
    measure_range: Tuple[int, int]  # (inicio, fin) en índices de compases

    def get_all_motifs(self) -> List[Motif]:
        """Retorna todos los motivos de la semifrase en orden."""
        motifs = []
        for phrase in self.phrases:
            motifs.extend(phrase.get_motifs())
        return motifs


@dataclass
class Period:
    """
    Período: antecedente + consecuente (típicamente 8 compases).

    El período es la estructura formal completa que implementa el principio
    de pregunta-respuesta en la música clásica.
    """
    antecedent: Semiphrase  # Semifrase antecedente (pregunta, termina en V)
    consequent: Semiphrase  # Semifrase consecuente (respuesta, termina en I)
    total_measures: int  # Número total de compases
    base_motif: Motif  # Motivo generador de todo el período
    harmonic_plan: List[HarmonicFunction]  # Plan armónico completo

    def get_all_motifs(self) -> List[Motif]:
        """Retorna todos los motivos del período en orden."""
        return self.antecedent.get_all_motifs() + self.consequent.get_all_motifs()

    def get_structure_summary(self) -> str:
        """Retorna un resumen de la estructura jerárquica."""
        return (
            f"Period ({self.total_measures} measures):\n"
            f"  Antecedent ({self.antecedent.cadence_type} cadence): "
            f"measures {self.antecedent.measure_range[0]+1}-{self.antecedent.measure_range[1]}\n"
            f"    Phrases: {len(self.antecedent.phrases)}\n"
            f"  Consequent ({self.consequent.cadence_type} cadence): "
            f"measures {self.consequent.measure_range[0]+1}-{self.consequent.measure_range[1]}\n"
            f"    Phrases: {len(self.consequent.phrases)}"
        )
