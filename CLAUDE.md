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
├── lilypond.py       # LilyPond output (LilyPondFormatter)
├── generation.py     # Period generation (PeriodGenerator)
├── architect.py      # Main orchestrator (MelodicArchitect)
└── cli.py            # CLI interface

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

## Extension Points

- **New modes**: Add to `MODE_CONFIG` dict in `scales.py`
- **New variations**: Add cases in `MotifGenerator._apply_variation()` in `motif.py`
- **New harmonic progressions**: Modify `HarmonyManager.create_harmonic_progression()` in `harmony.py`
- **New generation method**: Add method to `PeriodGenerator` in `generation.py`
