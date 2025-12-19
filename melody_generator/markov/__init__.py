"""
Paquete de cadenas de Markov para generación musical.

Implementa aprendizaje de patrones melódicos y rítmicos desde corpus.
Modularizado para mejor mantenibilidad (v3.5).
"""

# Base classes and utilities
from .base import (
    MarkovChain,
    BaseMarkovModel,
    # Diatonic filtering
    get_diatonic_pitch_classes,
    is_diatonic_interval,
    filter_diatonic_intervals,
    MAJOR_SCALE_PITCH_CLASSES,
    MINOR_SCALE_PITCH_CLASSES,
)

# Melodic models
from .melodic import (
    MelodicMarkovModel,
    EnhancedMelodicMarkovModel,
)

# Rhythmic models
from .rhythmic import RhythmicMarkovModel

# Harmonic context models
from .harmonic import (
    HarmonicContextMarkovModel,
    CadenceMarkovModel,
)

__all__ = [
    # Base
    "MarkovChain",
    "BaseMarkovModel",
    # Diatonic utilities
    "get_diatonic_pitch_classes",
    "is_diatonic_interval",
    "filter_diatonic_intervals",
    "MAJOR_SCALE_PITCH_CLASSES",
    "MINOR_SCALE_PITCH_CLASSES",
    # Melodic
    "MelodicMarkovModel",
    "EnhancedMelodicMarkovModel",
    # Rhythmic
    "RhythmicMarkovModel",
    # Harmonic
    "HarmonicContextMarkovModel",
    "CadenceMarkovModel",
]
