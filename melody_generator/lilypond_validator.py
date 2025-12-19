"""
LilyPond Input Validation Module.

Validates user-provided LilyPond notation by:
1. Compiling with LilyPond to verify syntax
2. Converting to MIDI
3. Loading into Music21 for musical analysis
4. Checking coherence with specified parameters (key, meter)

This module does NOT correct the input - it only validates.
If validation fails, the user should fix their input.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

try:
    from music21 import converter, stream, key, meter, analysis, pitch
except ImportError:
    converter = None
    stream = None
    key = None
    meter = None


@dataclass
class ValidationResult:
    """Result of validating LilyPond input."""

    is_valid: bool
    error_message: Optional[str] = None

    # Detected musical properties (if valid)
    detected_key: Optional[str] = None
    detected_mode: Optional[str] = None
    detected_meter_num: Optional[int] = None
    detected_meter_den: Optional[int] = None
    note_count: int = 0
    duration_beats: float = 0.0

    # Warnings (non-fatal issues)
    warnings: list = None

    # The music21 stream (for further processing)
    music21_stream: Any = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding music21 stream)."""
        return {
            "is_valid": self.is_valid,
            "error_message": self.error_message,
            "detected_key": self.detected_key,
            "detected_mode": self.detected_mode,
            "detected_meter_num": self.detected_meter_num,
            "detected_meter_den": self.detected_meter_den,
            "note_count": self.note_count,
            "duration_beats": self.duration_beats,
            "warnings": self.warnings,
        }


def wrap_lilypond_fragment(fragment: str, key_name: str = "c", mode: str = "major",
                            meter_num: int = 4, meter_den: int = 4) -> str:
    """
    Wrap a LilyPond fragment in a complete, compilable document.

    Args:
        fragment: User's LilyPond notation (e.g., "c'4 d' e' f' | g'2 e'")
        key_name: Key signature (LilyPond format, e.g., "c", "d", "fis")
        mode: Mode name (e.g., "major", "minor", "dorian")
        meter_num: Time signature numerator
        meter_den: Time signature denominator

    Returns:
        Complete LilyPond document string.
    """
    # Map mode to LilyPond mode name
    mode_map = {
        "major": "\\major",
        "minor": "\\minor",
        "dorian": "\\dorian",
        "phrygian": "\\phrygian",
        "lydian": "\\lydian",
        "mixolydian": "\\mixolydian",
        "locrian": "\\locrian",
        "harmonic_minor": "\\minor",  # LilyPond doesn't have harmonic minor mode
        "melodic_minor": "\\minor",
    }

    ly_mode = mode_map.get(mode.lower(), "\\major")

    # Convert key name to LilyPond format (lowercase, proper accidentals)
    ly_key = key_name.lower().replace("#", "is").replace("b", "es")

    document = f"""\\version "2.24.0"

\\header {{
  tagline = ""
}}

\\score {{
  \\new Staff {{
    \\key {ly_key} {ly_mode}
    \\time {meter_num}/{meter_den}
    {fragment}
  }}
  \\midi {{ }}
}}
"""
    return document


def validate_lilypond_syntax(fragment: str, key_name: str = "C", mode: str = "major",
                              meter_num: int = 4, meter_den: int = 4) -> ValidationResult:
    """
    Validate LilyPond syntax by attempting to compile it.

    This checks:
    1. LilyPond syntax is correct
    2. The notation produces valid MIDI output

    Args:
        fragment: User's LilyPond notation
        key_name: Expected key (for wrapping the fragment)
        mode: Expected mode
        meter_num: Expected meter numerator
        meter_den: Expected meter denominator

    Returns:
        ValidationResult with syntax validation outcome.
    """
    if not fragment or not fragment.strip():
        return ValidationResult(
            is_valid=False,
            error_message="No se proporcionó ningún código LilyPond"
        )

    # Wrap the fragment in a complete document
    full_document = wrap_lilypond_fragment(
        fragment.strip(),
        key_name=key_name,
        mode=mode,
        meter_num=meter_num,
        meter_den=meter_den
    )

    # Create temporary files for compilation
    with tempfile.TemporaryDirectory() as tmpdir:
        ly_path = Path(tmpdir) / "input.ly"
        output_base = Path(tmpdir) / "output"

        # Write the LilyPond file
        with open(ly_path, "w", encoding="utf-8") as f:
            f.write(full_document)

        # Try to compile with LilyPond
        try:
            result = subprocess.run(
                [
                    "lilypond",
                    "-dno-point-and-click",
                    f"--output={output_base}",
                    str(ly_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check for MIDI output
            midi_path = Path(str(output_base) + ".midi")

            if not midi_path.exists():
                # Compilation might have succeeded but no MIDI
                error_msg = result.stderr if result.stderr else "No se generó archivo MIDI"
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Error de LilyPond: {error_msg[:500]}"
                )

            # Now validate with Music21
            return validate_with_music21(midi_path, key_name, mode, meter_num, meter_den)

        except subprocess.TimeoutExpired:
            return ValidationResult(
                is_valid=False,
                error_message="Tiempo de compilación excedido (>30s)"
            )
        except FileNotFoundError:
            return ValidationResult(
                is_valid=False,
                error_message="LilyPond no está instalado o no está en PATH"
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"Error inesperado: {str(e)}"
            )


def validate_with_music21(midi_path: Path, expected_key: str, expected_mode: str,
                           expected_meter_num: int, expected_meter_den: int) -> ValidationResult:
    """
    Load MIDI into Music21 and analyze the musical content.

    Args:
        midi_path: Path to the MIDI file
        expected_key: Expected key signature
        expected_mode: Expected mode
        expected_meter_num: Expected meter numerator
        expected_meter_den: Expected meter denominator

    Returns:
        ValidationResult with detailed analysis.
    """
    if converter is None:
        # Music21 not available, just return basic validation
        return ValidationResult(
            is_valid=True,
            warnings=["Music21 no disponible - validación limitada"]
        )

    try:
        # Load the MIDI file
        score = converter.parse(str(midi_path))

        warnings = []

        # Count notes
        notes = list(score.flatten().notes)
        note_count = len(notes)

        if note_count == 0:
            return ValidationResult(
                is_valid=False,
                error_message="El motivo no contiene ninguna nota"
            )

        # Calculate total duration
        duration_beats = score.duration.quarterLength

        # Detect key using Krumhansl-Schmuckler
        detected_key_obj = score.analyze('key')
        detected_key = detected_key_obj.tonic.name if detected_key_obj else None
        detected_mode = detected_key_obj.mode if detected_key_obj else None

        # Check key match
        if detected_key and expected_key:
            # Normalize key names for comparison
            exp_key_normalized = expected_key.upper().replace("B", "B-").replace("#", "-sharp")
            det_key_normalized = detected_key.upper()

            if det_key_normalized != exp_key_normalized:
                # Allow relative major/minor matches
                warnings.append(
                    f"Tonalidad detectada ({detected_key} {detected_mode}) "
                    f"difiere de la especificada ({expected_key} {expected_mode})"
                )

        # Detect time signature from the first measure
        detected_meter_num = expected_meter_num
        detected_meter_den = expected_meter_den

        time_sigs = list(score.flatten().getElementsByClass('TimeSignature'))
        if time_sigs:
            ts = time_sigs[0]
            detected_meter_num = ts.numerator
            detected_meter_den = ts.denominator

        return ValidationResult(
            is_valid=True,
            detected_key=detected_key,
            detected_mode=detected_mode,
            detected_meter_num=detected_meter_num,
            detected_meter_den=detected_meter_den,
            note_count=note_count,
            duration_beats=duration_beats,
            warnings=warnings,
            music21_stream=score,
        )

    except Exception as e:
        return ValidationResult(
            is_valid=False,
            error_message=f"Error al analizar con Music21: {str(e)}"
        )


def quick_syntax_check(fragment: str) -> Tuple[bool, Optional[str]]:
    """
    Perform a quick syntax check on LilyPond notation without full compilation.

    This is a fast check for common errors before attempting full validation.

    Args:
        fragment: User's LilyPond notation

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not fragment or not fragment.strip():
        return False, "Entrada vacía"

    fragment = fragment.strip()

    # Check for balanced braces
    brace_count = fragment.count('{') - fragment.count('}')
    if brace_count != 0:
        return False, "Llaves no balanceadas"

    # Check for balanced brackets
    bracket_count = fragment.count('[') - fragment.count(']')
    if bracket_count != 0:
        return False, "Corchetes no balanceados"

    # Check for balanced parentheses
    paren_count = fragment.count('(') - fragment.count(')')
    if paren_count != 0:
        return False, "Paréntesis no balanceados"

    # Check for unclosed strings
    quote_count = fragment.count('"')
    if quote_count % 2 != 0:
        return False, "Comillas no cerradas"

    # Check for at least one note-like token
    # LilyPond notes are like: c, d, e, f, g, a, b (optionally with ', , or number)
    import re
    note_pattern = r'\b[a-g](is|es|isis|eses)?[\',]*\d*'
    if not re.search(note_pattern, fragment.lower()):
        return False, "No se detectaron notas válidas"

    return True, None


def validate_motif_for_development(
    fragment: str,
    key_name: str,
    mode: str,
    meter_num: int,
    meter_den: int,
) -> ValidationResult:
    """
    Full validation pipeline for user-provided motif.

    This is the main entry point for validating LilyPond input
    before developing it into a full melody.

    Args:
        fragment: User's LilyPond notation
        key_name: Expected key signature
        mode: Expected mode
        meter_num: Expected meter numerator
        meter_den: Expected meter denominator

    Returns:
        ValidationResult with complete validation outcome.
    """
    # Quick syntax check first
    is_valid, error = quick_syntax_check(fragment)
    if not is_valid:
        return ValidationResult(
            is_valid=False,
            error_message=f"Error de sintaxis: {error}"
        )

    # Full validation with LilyPond and Music21
    return validate_lilypond_syntax(
        fragment=fragment,
        key_name=key_name,
        mode=mode,
        meter_num=meter_num,
        meter_den=meter_den,
    )
