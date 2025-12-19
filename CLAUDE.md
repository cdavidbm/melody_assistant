# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Classical melody generator implementing music theory principles ("Protocolo Symmetry & Logic"). Modular Python package that generates LilyPond-compatible melodic output using music21 for musical logic and Abjad for notation formatting.

## Commands

```bash
# Install dependencies
pip install abjad music21

# Run the interactive melody generator
python3 main.py
# Or as module
python3 -m melody_generator
```

No tests or linting configured.

## Architecture

### Package Structure

```
melody_generator/
├── __init__.py       # Exports: MelodicArchitect, GenerationConfig, etc.
├── __main__.py       # Entry point for python -m melody_generator
├── config.py         # NEW: Dataclasses de configuración (SOLID: SRP)
├── protocols.py      # NEW: Interfaces/Protocolos ABC (SOLID: DIP, ISP)
├── loaders.py        # NEW: Factories para Markov (SOLID: SRP)
├── converters.py     # NEW: Conversores Abjad↔music21 (SOLID: SRP)
├── models.py         # Enums and dataclasses
├── scales.py         # Scale/mode management (ScaleManager)
├── harmony.py        # Harmonic progressions (HarmonyManager)
├── rhythm.py         # Rhythmic patterns (RhythmGenerator)
├── pitch.py          # Pitch selection (PitchSelector)
├── motif.py          # Motif creation/variation (MotifGenerator)
├── markov.py         # Markov chains (BaseMarkovModel, MelodicMarkovModel, EnhancedMelodicMarkovModel, RhythmicMarkovModel)
├── scoring.py        # Multi-criteria scoring (MelodicScorer, NoteCandidate, PhraseContour)
├── lilypond.py       # LilyPond output (LilyPondFormatter)
├── generation.py     # Period generation (PeriodGenerator)
├── architect.py      # Main orchestrator with DI (MelodicArchitect)
├── validation.py     # Music validation (MusicValidator, AutoCorrector)
└── cli.py            # CLI interface (refactored into functions)

models/               # Pre-trained Markov models
├── melody_markov/    # Melodic interval models
│   ├── bach_intervals.json
│   ├── mozart_intervals.json
│   ├── beethoven_intervals.json
│   └── combined_intervals.json
└── rhythm_markov/    # Rhythmic pattern models
    ├── bach_rhythms.json
    ├── mozart_rhythms.json
    ├── beethoven_rhythms.json
    └── combined_rhythms.json

scripts/
└── train_markov.py   # Script to train Markov models from corpus

main.py               # Wrapper for backwards compatibility
```

### 3-Layer Design

1. **Layer I - Musical Reality Configuration**: `scales.py`, `harmony.py`
2. **Layer II - DNA Generation**: `rhythm.py`, `pitch.py`, `motif.py`
3. **Layer III - Development & Closure**: `generation.py`, `lilypond.py`

### Two Generation Methods

- **Traditional** (`PeriodGenerator.generate_period()`): Rhythmic cohesion via single rhythmic motif
- **Hierarchical** (`PeriodGenerator.generate_period_hierarchical()`): Formal hierarchy (Motif → Phrase → Period)

## Key Modules

| Module | Class | Responsibility |
|--------|-------|----------------|
| `models.py` | - | Enums: `ImpulseType`, `NoteFunction`, `MotivicVariation`; Dataclasses: `Motif`, `RhythmicPattern`, `HarmonicFunction`, etc. |
| `scales.py` | `ScaleManager` | Scale configuration, pitch-to-degree conversion, melodic range |
| `harmony.py` | `HarmonyManager` | Harmonic function, chord tones, progressions |
| `rhythm.py` | `RhythmGenerator` | Beat subdivision, rhythmic patterns, strong beats |
| `pitch.py` | `PitchSelector` | Melodic pitch selection, contour control, climax |
| `motif.py` | `MotifGenerator` | Base motif creation, 6 variation types |
| `generation.py` | `PeriodGenerator` | Traditional and hierarchical generation |
| `lilypond.py` | `LilyPondFormatter` | Abjad-to-LilyPond conversion |
| `markov.py` | `BaseMarkovModel`, `MelodicMarkovModel`, `EnhancedMelodicMarkovModel`, `RhythmicMarkovModel` | Markov chain learning from music21 corpus |
| `scoring.py` | `MelodicScorer`, `NoteCandidate`, `PhraseContour` | Multi-criteria note selection with voice leading |
| `architect.py` | `MelodicArchitect` | Main entry point with DI support, orchestrates all modules |
| `cli.py` | - | Interactive CLI with refactored functions |
| `config.py` | `GenerationConfig`, `TonalConfig`, etc. | Dataclasses de configuración centralizada |
| `protocols.py` | Protocol classes | Interfaces para inyección de dependencias |
| `loaders.py` | `MarkovModelLoader` | Factory para carga de modelos Markov |
| `converters.py` | `AbjadMusic21Converter` | Conversiones entre Abjad y music21 |

## SOLID Architecture (v3.0)

### Principios Aplicados

| Principio | Implementación |
|-----------|----------------|
| **SRP** | `config.py` para configuración, `loaders.py` para carga, `converters.py` para conversión |
| **OCP** | Nuevos modos/variaciones se agregan sin modificar clases existentes |
| **LSP** | `BaseMarkovModel` → `MelodicMarkovModel`, `RhythmicMarkovModel` |
| **ISP** | Protocolos específicos: `PitchSelectorProtocol`, `RhythmGeneratorProtocol`, etc. |
| **DIP** | `MelodicArchitect` acepta dependencias inyectadas vía protocolos |

### Configuración Centralizada

```python
from melody_generator import GenerationConfig, TonalConfig, MeterConfig, MarkovConfig

# Modo 1: Configuración completa
config = GenerationConfig(
    tonal=TonalConfig(key_name="D", mode="dorian"),
    meter=MeterConfig(meter_tuple=(3, 4), num_measures=16),
    markov=MarkovConfig(enabled=True, composer="bach"),
)
architect = MelodicArchitect.from_config(config)

# Modo 2: API legacy (compatible)
architect = MelodicArchitect(key_name="C", mode="major", num_measures=8)

# Modo 3: Factory con defaults
architect = MelodicArchitect.with_defaults()
```

### Inyección de Dependencias

```python
from melody_generator import MelodicArchitect
from melody_generator.scales import ScaleManager

# Inyectar dependencia personalizada
custom_scale = ScaleManager("C", "major")
architect = MelodicArchitect(
    config=config,
    scale_manager=custom_scale,  # Inyectado
)
```

## Critical Conventions

### LilyPond Notation
Use **standard LilyPond notation** (Dutch), not English:
- Sharps: `cis`, `dis`, `fis` (NOT `cs`, `ds`, `fs`)
- Flats: `bes`, `es`, `as` (NOT `bf`, `ef`, `af`)
- `LilyPondFormatter.english_to_standard_pitch()` handles conversion

### Abjad API
- Notes: `"c'4"` (pitch + duration)
- Octaves: `c,` = C2, `c` = C3, `c'` = C4, `c''` = C5
- Durations: `1` = whole, `2` = half, `4` = quarter, `8` = eighth
- **Notes in Container cannot be reused**; always create new instances

### Code Style
- Classes: PascalCase (`MelodicArchitect`, `ScaleManager`)
- Methods/variables: snake_case (`get_pitch_by_degree`)
- Enums: SCREAMING_SNAKE_CASE (`ImpulseType.TETIC`)
- Imports: stdlib → music21 → abjad → local modules

## 21 Supported Modes

Diatonic (7): major, minor, dorian, phrygian, lydian, mixolydian, locrian
Minor scales (2): harmonic_minor, melodic_minor
Harmonic minor modes (7): locrian_nat6, ionian_aug5, dorian_sharp4, phrygian_dominant, lydian_sharp2, superlocrian_bb7
Melodic minor modes (7): dorian_flat2, lydian_augmented, lydian_dominant, mixolydian_flat6, locrian_nat2, altered

## Markov Chains (New Feature)

### Overview

The system now includes **optional** Markov chain support for learning melodic and rhythmic patterns from classical composers (Bach, Mozart, Beethoven). Markov chains generate more idiomatic, natural-sounding melodies by learning probability distributions of intervals and rhythms from the music21 corpus.

### Key Characteristics

- **Completely Optional**: Default behavior unchanged (`use_markov=False`)
- **Subordinate to Theory**: Markov suggestions respect harmonic and formal rules
- **Pre-trained Models**: 8 models included (~220KB total)
  - Melodic: Bach (17k transitions), Mozart (3.7k), Beethoven (38k), Combined (59k)
  - Rhythmic: Bach (19k transitions), Mozart (3.8k), Beethoven (39k), Combined (62k)
- **Order 2 Default**: Considers 2 previous states for context
- **Weight Configurable**: 0.0 (ignore Markov) to 1.0 (maximum influence)

### Usage in CLI

When running `python main.py`, new interactive prompts appear:

```
=== CADENAS DE MARKOV (Aprendizaje de Compositores Clásicos) ===

¿Usar cadenas de Markov? (s/n) [n]: s

Compositor de referencia:
1. Bach (363 obras - estilo contrapuntístico)
2. Mozart (11 obras - estilo clásico elegante)
3. Beethoven (23 obras - estilo dramático)
4. Combinado (mezcla de los tres estilos)
Seleccione compositor [1]: 1

Peso de Markov (0.0-1.0) [0.5]: 0.6
Orden de la cadena [2]: 2
```

### Usage Programmatically

```python
from melody_generator.architect import MelodicArchitect

# With Markov enabled
architect = MelodicArchitect(
    key_name="C",
    mode="major",
    num_measures=8,
    use_markov=True,           # Enable Markov chains
    markov_composer="bach",    # "bach", "mozart", "beethoven", "combined"
    markov_weight=0.5,         # 0.0-1.0 (influence level)
    markov_order=2             # 1-3 (context depth)
)

staff = architect.generate_period()
```

### Enhanced Markov Model (v3.1)

The `EnhancedMelodicMarkovModel` provides richer state representation:

- **State**: `(degree, metric, direction)` instead of just interval
  - `degree`: Scale degree (1-7)
  - `metric`: "strong" or "weak" beat
  - `direction`: 1 (ascending), 0 (static), -1 (descending)
- **Soprano-only extraction**: Trains only on melody line, not all voices
- **Degree probabilities**: Returns probabilities per scale degree

```python
from melody_generator import EnhancedMelodicMarkovModel

# Train enhanced model
model = EnhancedMelodicMarkovModel(order=2, composer="bach")
model.train_from_corpus(composer="bach", voice_part=0)  # soprano only

# Get probabilities for each degree
probs = model.get_degree_probabilities(current_metric="strong")
# Returns: {1: 0.15, 2: 0.08, 3: 0.12, 4: 0.05, 5: 0.25, 6: 0.10, 7: 0.08}
```

Train with: `python scripts/train_markov.py --composer bach --type melody --enhanced`

## Multi-Criteria Scoring System (v3.1)

The `MelodicScorer` replaces random note selection with intelligent scoring:

### Scoring Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Voice Leading | 28% | Prefer stepwise motion (seconds > thirds > larger) |
| Harmonic | 22% | Chord tones on strong beats |
| Contour | 15% | Follow planned phrase shape |
| Tendency | 12% | Resolve tendency tones (7→1, 4→3) |
| Markov | 10% | Composer-learned patterns (if enabled) |
| Variety | 8% | Avoid excessive repetition |
| Range | 5% | Prefer center of melodic range |

### Phrase Planning

Each phrase has a planned contour:
- **Antecedent**: Climax at ~60%, ends on dominant (5)
- **Consequent**: Climax at ~50%, ends on tonic (1)

```python
from melody_generator.scoring import PhraseContour

contour = PhraseContour(
    length=16,           # Notes in phrase
    start_degree=1,      # Start on tonic
    climax_position=0.6, # Climax at 60%
    climax_degree=5,     # Reach dominant
    end_degree=1,        # End on tonic
)
contour.plan_targets()
# contour.target_degrees = [1, 1, 2, 3, 4, 5, 4, 3, 2, 1, ...]
```

### Training New Models

To retrain models from music21 corpus:

```bash
# Train all composers (melody + rhythm)
python scripts/train_markov.py --composer all --type both --order 2

# Train specific composer
python scripts/train_markov.py --composer bach --type melody --order 2

# Train with limited works (for testing)
python scripts/train_markov.py --composer mozart --type both --max-works 5
```

### Implementation Details

#### Melodic Markov (`MelodicMarkovModel`)
- **State**: Interval in semitones (-12 to +12)
- **Application**: Ornamental notes (passing tones, neighbors)
- **Subordination**: Structural notes (chord tones) always follow harmonic rules
- **Location**: `pitch.py:142-190` (ornamental note selection)

#### Rhythmic Markov (`RhythmicMarkovModel`)
- **State**: Duration tuple `(numerator, denominator)` e.g. `(1, 4)` = quarter note
- **Application**: Weak beat subdivisions
- **Subordination**: Strong beats maintain metric hierarchy
- **Location**: `rhythm.py:92-115` (beat subdivision)

#### Model Loading (`architect.py`)
- Models loaded from `models/melody_markov/` and `models/rhythm_markov/`
- Automatic fallback if models missing (warning printed, generation continues)
- Models passed to `PitchSelector` and `RhythmGenerator` at initialization

## Validation & Correction System (New Feature)

The system now includes **automatic validation and iterative correction** to ensure generated melodies actually fulfill their musical specifications.

### Key Characteristics

- **Always Active**: All melodies are automatically validated
- **Iterative Correction**: Identifies specific problems and fixes them without regenerating from scratch
- **User Control**: User decides whether to accept, retry with corrections, or cancel
- **No Limits**: Infinite retry attempts until user is satisfied

### How It Works

1. **Generation**: System generates melody with current parameters
2. **Validation**: music21 analyzes the melody for:
   - **Key/Tonality**: Krumhansl-Schmuckler algorithm + diatonic percentage
   - **Meter**: Measure durations match time signature
   - **Range**: Melodic ambitus is singable (<= 24 semitones)
   - **Mode**: Modal characteristics are present
3. **Report**: Beautiful ASCII art report shows all validation results
4. **Correction**: If invalid, AutoCorrector suggests specific parameter adjustments
5. **User Choice**:
   - Option 1: Apply corrections and retry (modifies parameters, regenerates)
   - Option 2: Accept current melody (even if invalid)
   - Option 3: Cancel and exit

### CLI Usage

When running `python main.py`, new validation prompts appear:

```
=== VALIDACIÓN MUSICAL ===

El sistema validará automáticamente que la melodía generada
cumpla con las especificaciones de tonalidad, métrica y rango.

Nivel de exigencia en validación:
1. Estricto (80-90% de precisión)
2. Moderado (60-70% de precisión) [Recomendado]
3. Permisivo (40-50% de precisión)
Seleccione nivel [2]: 2
```

After generation, validation report appears:

```
╔════════════════════════════════════════════════════════════════════╗
║                    REPORTE DE VALIDACIÓN                           ║
╚════════════════════════════════════════════════════════════════════╝

Estado General: ⚠️ REQUIERE ATENCIÓN
Puntuación:     72.3% (calidad musical)

┌─ TONALIDAD ───────────────────────────────────────────────────────┐
│ Esperada:         C major                                          │
│ Detectada:        C major                                          │
│ Correlación:      85.2% (certeza del análisis)                    │
│ Notas diatónicas: 89.3%                                           │
│ Estado:           ✓ COINCIDE                                       │
└────────────────────────────────────────────────────────────────────┘

🔧 Correcciones sugeridas:
  • Reforzar cadencias para establecer tonalidad

Opciones:
  1. Aplicar correcciones e intentar de nuevo
  2. Aceptar melodía actual (aunque no sea válida)
  3. Cancelar y salir
  
Seleccione opción [1]:
```

### Programmatic Usage

```python
from melody_generator import MelodicArchitect
from melody_generator.validation import MusicValidator, AutoCorrector

# Generate melody
architect = MelodicArchitect(key_name="C", mode="major", num_measures=8)
staff = architect.generate_period()

# Validate
validator = MusicValidator(
    staff=staff,
    lilypond_formatter=architect.lilypond_formatter,
    expected_key="C",
    expected_mode="major",
    expected_meter=(4, 4),
    tolerance=0.65  # 65% threshold
)

report = validator.validate_all()
print(report.format_detailed_report())

# If invalid, get corrections
if not report.is_valid:
    corrector = AutoCorrector(report)
    
    # Get suggested parameter adjustments
    architect_params = {
        "key_name": "C",
        "mode": "major",
        "rhythmic_complexity": 2,
        "max_interval": 6,
        "infraction_rate": 0.1,
    }
    
    # Apply corrections
    corrected_params = corrector.apply_to_architect_params(architect_params)
    
    # Regenerate with corrected parameters
    architect = MelodicArchitect(**corrected_params)
    staff = architect.generate_period()
```

### Correction Strategies

The `AutoCorrector` applies these corrections based on detected problems:

| Problem | Correction |
|---------|------------|
| **Key mismatch** | Reduce `infraction_rate` (less chromatic notes) |
| **Low diatonic %** | Reduce `infraction_rate` by 50% |
| **Meter errors** | Reduce `rhythmic_complexity` by 1 level |
| **Range too wide** | Reduce `max_interval` to 4 semitones |
| **Range too narrow** | (Currently no automatic correction) |

### Implementation Files

- `melody_generator/validation.py` (~850 lines)
  - `MusicValidator`: Main validator class
  - `ValidationReport`: Detailed report with ASCII formatting
  - `AutoCorrector`: Parameter adjustment engine
- `melody_generator/cli.py` (modified)
  - Interactive validation loop
  - User choice prompts
- `output/` directory: Auto-saved melodies (timestamped)

### Extension Points

- **New modes**: Add to `MODE_CONFIG` dict in `scales.py`
- **New variations**: Add cases in `MotifGenerator._apply_variation()` in `motif.py`
- **New harmonic progressions**: Modify `HarmonyManager.create_harmonic_progression()` in `harmony.py`
- **New generation method**: Add method to `PeriodGenerator` in `generation.py`
- **New Markov composers**: Train models with `scripts/train_markov.py` and place in `models/`
- **Custom corpus**: Modify `MelodicMarkovModel.train_from_corpus()` to accept custom MIDI/MusicXML files
- **New validation metrics**: Add methods to `MusicValidator` in `validation.py`
- **New correction strategies**: Extend `AutoCorrector._correct_*_issues()` methods
