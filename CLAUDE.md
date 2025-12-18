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
├── __init__.py       # Exports: MelodicArchitect, ImpulseType, etc.
├── __main__.py       # Entry point for python -m melody_generator
├── models.py         # Enums and dataclasses
├── scales.py         # Scale/mode management (ScaleManager)
├── harmony.py        # Harmonic progressions (HarmonyManager)
├── rhythm.py         # Rhythmic patterns (RhythmGenerator)
├── pitch.py          # Pitch selection (PitchSelector)
├── motif.py          # Motif creation/variation (MotifGenerator)
├── markov.py         # Markov chains (MarkovChain, MelodicMarkovModel, RhythmicMarkovModel)
├── lilypond.py       # LilyPond output (LilyPondFormatter)
├── generation.py     # Period generation (PeriodGenerator)
├── architect.py      # Main orchestrator (MelodicArchitect)
└── cli.py            # CLI interface

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
| `markov.py` | `MarkovChain`, `MelodicMarkovModel`, `RhythmicMarkovModel` | Markov chain learning from music21 corpus |
| `architect.py` | `MelodicArchitect` | Main entry point, orchestrates all modules |
| `cli.py` | - | Interactive command-line interface |

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

### Extension Points

- **New modes**: Add to `MODE_CONFIG` dict in `scales.py`
- **New variations**: Add cases in `MotifGenerator._apply_variation()` in `motif.py`
- **New harmonic progressions**: Modify `HarmonyManager.create_harmonic_progression()` in `harmony.py`
- **New generation method**: Add method to `PeriodGenerator` in `generation.py`
- **New Markov composers**: Train models with `scripts/train_markov.py` and place in `models/`
- **Custom corpus**: Modify `MelodicMarkovModel.train_from_corpus()` to accept custom MIDI/MusicXML files
