"""
Generador de Melodías Clásicas - Protocolo "Symmetry & Logic"

Implementación computacional de los principios de composición melódica
de la teoría musical clásica, con soporte para métricas regulares y
amalgama, 21 modos musicales, y dos métodos de generación.
"""

from .models import (
    ImpulseType,
    NoteFunction,
    MotivicVariation,
    RhythmicPattern,
    Motif,
    MelodicContour,
    HarmonicFunction,
    Phrase,
    Semiphrase,
    Period,
)
from .architect import MelodicArchitect

__version__ = "2.0.0"
__all__ = [
    "MelodicArchitect",
    "ImpulseType",
    "NoteFunction",
    "MotivicVariation",
    "RhythmicPattern",
    "Motif",
    "MelodicContour",
    "HarmonicFunction",
    "Phrase",
    "Semiphrase",
    "Period",
]
