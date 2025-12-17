# AGENTS.md - Classical Music Melody Generator

## Build/Run Commands
- **Run interactive mode**: `python3 main.py` (guides through 12 config steps)
- **Install dependencies**: `pip install abjad music21`
- **Compile LilyPond**: `lilypond output.ly` (generates PDF + MIDI)
- **No tests**: This is a single-file generative tool, no test suite

## Project Structure
- `main.py` - Single-file generator (MelodicArchitect class, ~1530 lines)
- `tarea.md` - Music theory specification (Spanish)
- `README.md` - Complete user documentation
- `showcase_final.ly` - Example output (F Dorian, 7/8 time)

## Code Style Guidelines

### Imports
- Standard library (random, enum, dataclasses, typing)
- music21 (key, pitch, interval, scale)
- abjad (for LilyPond generation)
- Order: stdlib → music21 → abjad

### Naming Conventions
- **Classes**: PascalCase (`MelodicArchitect`, `ImpulseType`, `NoteFunction`)
- **Methods**: snake_case (`get_pitch_by_degree`, `create_measure`, `generate_period`)
- **Variables**: snake_case, descriptive (`strong_beats`, `is_cadence`, `harmonic_function`)
- **Enums**: SCREAMING_SNAKE_CASE for values (`ImpulseType.TETIC`)

### Code Organization
- **3-Layer Architecture**:
  1. Configuración de Realidad Musical (tonalidad, métrica, parámetros)
  2. Generación del ADN Melódico (motivos, ritmos, selección de tonos)
  3. Desarrollo y Cierre (períodos, cadencias, output)
- Use dataclasses for data structures (`RhythmicPattern`, `MelodicContour`)
- Separate music21 (musical logic) from abjad (output formatting)

### Abjad API Specifics
- `abjad.Note()` takes string format: `"c'4"` (pitch + duration)
- Pitch format: `c'` = C4, `c''` = C5, `c` = C3, `c,` = C2
- Flats use 'f' (`ef` = Eb), sharps use 's' (`cs` = C#)
- Duration: number after pitch (4 = quarter, 8 = eighth, 2 = half, 1 = whole)
- Dotted notes: append dot (`c'4.` = dotted quarter)
- Notes in Container cannot be reused; create new instances

### Music Theory Implementation
- **Structural notes** on strong beats (chord tones: I, III, V)
- **Passing notes** on weak beats (stepwise motion)
- **Cadences**: Half cadence (ends on V), Authentic (V→I)
- **Infraction/Compensation**: Probabilistic rule-breaking with automatic compensation
- **Amalgam meters**: Subdivisions define strong beats (e.g., 5/8 = [2,3])
- **Musical rests**: Strategic silence placement for breathing, articulation, and rhythmic impulses
  - Phrase-end respirations (higher probability)
  - Anacroustic impulses (rests before downbeat)
  - Acephalous patterns (rests on downbeat)
  - Decorative rests (lower probability on weak beats)
- **Motivic variations**: Classical techniques for thematic development
  - Inversion (intervals flip direction)
  - Retrograde (motif backwards)
  - Augmentation/Diminution (rhythmic stretching/compression)
  - Transposition and sequences
  - Contextual application based on climax proximity
- **Melodic climax control**: Explicit management of highest point
  - Configurable position (0.0-1.0 of piece)
  - Gradual approach over 3 measures
  - Expanded register (higher octaves)
  - Tracking of highest pitch reached

### LilyPond Output Format
- Output wrapped in `\score { ... }` block
- Automatic `\midi {}` block for MIDI file generation
- Compatible with Frescobaldi and standalone LilyPond
- **CRITICAL**: Use standard LilyPond notation (is/es, not s/f)
  - Sharps: `cis`, `dis`, `fis` (not `cs`, `ds`, `fs`)
  - Flats: `bes`, `es`, `as` (not `bf`, `ef`, `af`)
  - Method `_english_to_standard_pitch()` handles conversion (main.py:1140-1184)

## Recent Updates (Dec 2025)
- ✅ Interactive mode with 12-step configuration
- ✅ File save option (auto-generate .ly files)
- ✅ Leap recovery (contrary motion after jumps >M3)
- ✅ Melodic range control (tonic octave ± P4)
- ✅ Tenoris system (quinta as nota tenens, Gregorian tradition)
- ✅ Standard LilyPond notation (Dutch: is/es)
- ✅ Professional output format (header, strict beaming)
- ✅ **Rhythm anchored to beats** (no involuntary syncopation)
- ✅ **Rhythmic motif consistency** (melodic cohesion via material economy)

## Cohesion and Phrasing System
- **Beat-by-beat rhythm generation**: Each beat is an indivisible unit, respects strong/weak hierarchy
- **Base rhythmic motif**: ONE pattern generated at start, reused throughout piece
- **Subtle variations**: Retrograde applied in 30% of measures (except cadences)
- **Structure**: Bars 1-2 (establish identity), 3-6 (variations), 7-8 (original for cadences)
- **Result**: Organic, singable, memorable melodies with clear identity
- **Principle** (tarea.md lines 128-130): "Economy of materials - don't invent new rhythms constantly"
