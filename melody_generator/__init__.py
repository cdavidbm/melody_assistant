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

Características expresivas (v3.2.0):
- ornamentation.py: Ornamentos estilísticos
- dynamics.py: Dinámicas automáticas
- articulation.py: Articulaciones y fraseo
- cadences.py: Gestos cadenciales específicos
- forms.py: Formas musicales (binaria, ternaria, rondó)
- modulation.py: Modulación a tonalidades relacionadas
- development.py: Desarrollo motívico avanzado
- sequences.py: Secuencias melódicas
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

# Clase principal y configuración de expresión
from .architect import MelodicArchitect, ExpressionConfig

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
    EnhancedMelodicMarkovModel,
    RhythmicMarkovModel,
    HarmonicContextMarkovModel,
    CadenceMarkovModel,
)

# Sistema de scoring
from .scoring import (
    MelodicScorer,
    NoteCandidate,
    PhraseContour,
    PhrasePosition,
    MetricStrength,
)

# Ornamentación
from .ornamentation import (
    OrnamentGenerator,
    OrnamentConfig,
    OrnamentStyle,
    OrnamentType,
    Ornament,
)

# Dinámicas
from .dynamics import (
    DynamicGenerator,
    DynamicLevel,
    DynamicChange,
    DynamicMark,
    DynamicPlan,
)

# Articulaciones
from .articulation import (
    ArticulationGenerator,
    ArticulationType,
    ArticulationMark,
    SlurMark,
)

# Cadencias
from .cadences import (
    CadenceGenerator,
    CadenceType,
    CadenceStrength,
    CadentialGesture,
)

# Formas musicales
from .forms import (
    FormGenerator,
    FormType,
    FormPlan,
    FormSection,
    SectionCharacter,
)

# Modulación
from .modulation import (
    ModulationGenerator,
    ModulationType,
    ModulationPlan,
    KeyRelationship,
)

# Desarrollo motívico
from .development import (
    MotivicDeveloper,
    DevelopmentTechnique,
    DevelopmentPlan,
)

# Secuencias
from .sequences import (
    SequenceGenerator,
    SequenceType,
    MelodicSequence,
)

__version__ = "3.2.0"
__all__ = [
    # Clase principal
    "MelodicArchitect",
    "ExpressionConfig",
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
    "EnhancedMelodicMarkovModel",
    "RhythmicMarkovModel",
    "HarmonicContextMarkovModel",
    "CadenceMarkovModel",
    # Scoring
    "MelodicScorer",
    "NoteCandidate",
    "PhraseContour",
    "PhrasePosition",
    "MetricStrength",
    # Ornamentación
    "OrnamentGenerator",
    "OrnamentConfig",
    "OrnamentStyle",
    "OrnamentType",
    "Ornament",
    # Dinámicas
    "DynamicGenerator",
    "DynamicLevel",
    "DynamicChange",
    "DynamicMark",
    "DynamicPlan",
    # Articulaciones
    "ArticulationGenerator",
    "ArticulationType",
    "ArticulationMark",
    "SlurMark",
    # Cadencias
    "CadenceGenerator",
    "CadenceType",
    "CadenceStrength",
    "CadentialGesture",
    # Formas musicales
    "FormGenerator",
    "FormType",
    "FormPlan",
    "FormSection",
    "SectionCharacter",
    # Modulación
    "ModulationGenerator",
    "ModulationType",
    "ModulationPlan",
    "KeyRelationship",
    # Desarrollo motívico
    "MotivicDeveloper",
    "DevelopmentTechnique",
    "DevelopmentPlan",
    # Secuencias
    "SequenceGenerator",
    "SequenceType",
    "MelodicSequence",
    # Utilidades
    "MarkovModelLoader",
    "AbjadMusic21Converter",
]
