"""
Generador de Melodías Clásicas - Protocolo "Symmetry & Logic"

Implementación computacional de los principios de composición melódica
de la teoría musical clásica, con soporte para métricas regulares y
amalgama, 21 modos musicales, y dos métodos de generación.

Arquitectura SOLID:
- config.py: Dataclasses de configuración centralizada
- protocols.py: Interfaces/Protocolos para inyección de dependencias
- loaders.py: Factories para carga de modelos
- converters.py: Conversores de formato Abjad↔music21
"""

# Modelos de datos
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

# Configuración centralizada
from .config import (
    TonalConfig,
    MeterConfig,
    RhythmConfig,
    MelodyConfig,
    MotifConfig,
    MarkovConfig,
    ValidationConfig,
    OutputConfig,
    GenerationConfig,
)

# Clase principal
from .architect import MelodicArchitect

# Validación
from .validation import (
    MusicValidator,
    ValidationReport,
    KeyValidation,
    MeterValidation,
    RangeValidation,
    ModeValidation,
    AutoCorrector,
)

# Factories y utilidades
from .loaders import MarkovModelLoader
from .converters import AbjadMusic21Converter

# Modelos Markov
from .markov import (
    MarkovChain,
    BaseMarkovModel,
    MelodicMarkovModel,
    RhythmicMarkovModel,
)

__version__ = "3.0.0"
__all__ = [
    # Clase principal
    "MelodicArchitect",
    # Configuración
    "GenerationConfig",
    "TonalConfig",
    "MeterConfig",
    "RhythmConfig",
    "MelodyConfig",
    "MotifConfig",
    "MarkovConfig",
    "ValidationConfig",
    "OutputConfig",
    # Modelos de datos
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
    # Validación
    "MusicValidator",
    "ValidationReport",
    "KeyValidation",
    "MeterValidation",
    "RangeValidation",
    "ModeValidation",
    "AutoCorrector",
    # Markov
    "MarkovChain",
    "BaseMarkovModel",
    "MelodicMarkovModel",
    "RhythmicMarkovModel",
    # Utilidades
    "MarkovModelLoader",
    "AbjadMusic21Converter",
]
