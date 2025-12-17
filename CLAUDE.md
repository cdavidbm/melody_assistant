# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Classical melody generator implementing music theory principles ("Protocolo Symmetry & Logic"). Single-file Python application (~2700 lines) that generates LilyPond-compatible melodic output using music21 for musical logic and Abjad for notation formatting.

## Commands

```bash
# Install dependencies
pip install abjad music21

# Run the interactive melody generator
python3 main.py
```

No tests or linting configured.

## Architecture

**Single class design**: `MelodicArchitect` in `main.py` contains all functionality in a 3-layer architecture:

1. **Layer I - Musical Reality Configuration**: Scale/mode setup (music21), meter/subdivisions, control parameters
2. **Layer II - DNA Generation**: Motif creation, rhythmic patterns, pitch selection (structural vs. passing notes)
3. **Layer III - Development & Closure**: Period structure, cadences, LilyPond output (Abjad)

**Two generation methods**:
- **Traditional** (`generate_period()`): Rhythmic cohesion via single rhythmic motif, 70% original + 30% retrograde variation
- **Hierarchical** (`generate_period_hierarchical()`): Formal hierarchy (Motif → Phrase → Period) with 6 variation types and configurable freedom levels

## Key Code Locations

| Feature | Method |
|---------|--------|
| Data structures | Lines 93-161 (dataclasses: Motif, Phrase, Period, etc.) |
| Mode intervals | `MODE_INTERVALS` dict (~line 50) |
| Motif creation | `create_base_motif()` |
| Harmonic progression | `create_harmonic_progression()` |
| Motif variations | `apply_motif_variation()` |
| Traditional generation | `generate_period()` |
| Hierarchical generation | `generate_period_hierarchical()` |
| LilyPond formatting | `_format_as_lilypond()` |
| Pitch conversion | `_english_to_standard_pitch()` |

## Critical Conventions

### LilyPond Notation
Use **standard LilyPond notation** (Dutch), not English:
- Sharps: `cis`, `dis`, `fis` (NOT `cs`, `ds`, `fs`)
- Flats: `bes`, `es`, `as` (NOT `bf`, `ef`, `af`)
- The `_english_to_standard_pitch()` method handles this conversion

### Abjad API
- Notes take string format: `"c'4"` (pitch + duration)
- Pitch octaves: `c,` = C2, `c` = C3, `c'` = C4, `c''` = C5
- Durations: `1` = whole, `2` = half, `4` = quarter, `8` = eighth
- Dotted notes: append dot (`c'4.`)
- **Notes in Container cannot be reused**; always create new instances

### Code Style
- Classes: PascalCase (`MelodicArchitect`, `ImpulseType`)
- Methods/variables: snake_case (`get_pitch_by_degree`, `strong_beats`)
- Enums: SCREAMING_SNAKE_CASE values (`ImpulseType.TETIC`)
- Import order: stdlib → music21 → abjad

## 21 Supported Modes

Diatonic (7): major, minor, dorian, phrygian, lydian, mixolydian, locrian
Minor scales (2): harmonic_minor, melodic_minor
Harmonic minor modes (7): locrian_nat6, ionian_aug5, dorian_sharp4, phrygian_dominant, lydian_sharp2, superlocrian_bb7
Melodic minor modes (7): dorian_flat2, lydian_augmented, lydian_dominant, mixolydian_flat6, locrian_nat2, altered

## Extension Points

- **New modes**: Add to `MODE_INTERVALS` dictionary
- **New variations**: Add cases in `apply_motif_variation()`
- **New harmonic progressions**: Modify `create_harmonic_progression()`
- **New generation method**: Create method similar to `generate_period_hierarchical()`
