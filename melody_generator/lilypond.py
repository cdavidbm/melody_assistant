"""
Formateo de salida LilyPond.
Convierte estructuras musicales a código LilyPond compatible.
"""

from typing import Tuple, Optional

import abjad
from music21 import pitch, key

from .scales import ScaleManager


class LilyPondFormatter:
    """
    Formatea la salida musical a código LilyPond.
    """

    def __init__(self, scale_manager: ScaleManager, mode: str, meter_tuple: Tuple[int, int]):
        """
        Inicializa el formateador.

        Args:
            scale_manager: Gestor de escalas
            mode: Modo musical
            meter_tuple: Compás (numerador, denominador)
        """
        self.scale_manager = scale_manager
        self.mode = mode
        self.meter_tuple = meter_tuple

    def convert_to_abjad_pitch(self, pitch_str: str) -> str:
        """
        Convierte un pitch de music21 a formato estándar LilyPond.

        Args:
            pitch_str: String de pitch en formato music21 (ej: "c4", "c#4", "eb5")

        Returns:
            String de pitch en formato LilyPond estándar
        """
        p = pitch.Pitch(pitch_str)
        base_name = p.step.lower()

        alteration = p.alter
        if alteration == 0:
            accidental_suffix = ""
        elif alteration == 1:
            accidental_suffix = "s"
        elif alteration == -1:
            accidental_suffix = "f"
        elif alteration == 2:
            accidental_suffix = "ss"
        elif alteration == -2:
            accidental_suffix = "ff"
        else:
            if alteration > 0:
                accidental_suffix = "s" * int(abs(alteration))
            else:
                accidental_suffix = "f" * int(abs(alteration))

        note_name = f"{base_name}{accidental_suffix}"

        octave = p.octave
        if octave == 3:
            octave_mark = ""
        elif octave < 3:
            octave_mark = "," * (3 - octave)
        else:
            octave_mark = "'" * (octave - 3)

        return f"{note_name}{octave_mark}"

    def english_to_standard_pitch(self, english_pitch: str) -> str:
        """
        Convierte notación inglesa de Abjad a notación estándar LilyPond.

        Args:
            english_pitch: Pitch en notación inglesa (ej: "bf", "cs", "c")

        Returns:
            Pitch en notación estándar (ej: "bes", "cis", "c")
        """
        base = english_pitch[0]
        rest = english_pitch[1:]

        accidental = ""
        octave = ""

        for char in rest:
            if char in ["'", ","]:
                octave += char
            else:
                accidental += char

        if not accidental:
            standard_accidental = ""
        elif accidental == "s":
            standard_accidental = "is"
        elif accidental == "ss":
            standard_accidental = "isis"
        elif accidental == "f":
            if base == "a":
                standard_accidental = "s"
            elif base == "e":
                standard_accidental = "s"
            else:
                standard_accidental = "es"
        elif accidental == "ff":
            if base in ["a", "e"]:
                standard_accidental = "ses"
            else:
                standard_accidental = "eses"
        else:
            standard_accidental = accidental

        return f"{base}{standard_accidental}{octave}"

    def to_absolute_lilypond(self, staff: abjad.Staff) -> str:
        """
        Convierte un Staff de Abjad a código LilyPond con notación absoluta.

        Returns:
            String con código LilyPond usando notación absoluta
        """
        leaves = list(abjad.select.leaves(staff))

        if not leaves:
            return "{ }"

        lily_elements = []

        for i, leaf in enumerate(leaves):
            if isinstance(leaf, abjad.Note):
                pitch_obj = leaf.written_pitch()
                pitch_str_english = pitch_obj._get_lilypond_format()
                pitch_str = self.english_to_standard_pitch(pitch_str_english)
                duration_obj = leaf.written_duration()

                numerator = duration_obj.numerator
                denominator = duration_obj.denominator

                if numerator == 1:
                    lily_duration = str(denominator)
                elif numerator == 3:
                    dotted_map = {
                        2: "1", 4: "2", 8: "4", 16: "8", 32: "16", 64: "32"
                    }
                    lily_duration = dotted_map.get(denominator, str(denominator)) + "."
                else:
                    lily_duration = str(denominator)

                lily_elements.append(f"{pitch_str}{lily_duration}")

            elif isinstance(leaf, abjad.Rest):
                duration_obj = leaf.written_duration()
                numerator = duration_obj.numerator
                denominator = duration_obj.denominator

                if numerator == 1:
                    lily_duration = str(denominator)
                elif numerator == 3:
                    dotted_map = {2: "1", 4: "2", 8: "4", 16: "8", 32: "16", 64: "32"}
                    lily_duration = dotted_map.get(denominator, str(denominator)) + "."
                else:
                    lily_duration = str(denominator)

                lily_elements.append(f"r{lily_duration}")

            indicators = abjad.get.indicators(leaf)
            for indicator in indicators:
                if isinstance(indicator, abjad.BarLine):
                    if indicator.abbreviation == "|.":
                        lily_elements.append('\\bar "|."')
                    else:
                        lily_elements.append("|")

        output_lines = []
        current_line = []
        elements_per_line = 6

        for elem in lily_elements:
            current_line.append(elem)
            if len(current_line) >= elements_per_line or "\\bar" in elem or elem == "|":
                output_lines.append(" ".join(current_line))
                current_line = []

        if current_line:
            output_lines.append(" ".join(current_line))

        formatted_code = "\n    ".join(output_lines)
        return f"{{\n    {formatted_code}\n  }}"

    def create_key_signature(self) -> Optional[abjad.KeySignature]:
        """Crea un objeto KeySignature de Abjad."""
        tonic = self.scale_manager.get_tonic()
        base_name = tonic.step.lower()

        alteration = tonic.alter
        if alteration == 0:
            accidental_suffix = ""
        elif alteration == 1:
            accidental_suffix = "is"
        elif alteration == -1:
            if base_name == "a":
                accidental_suffix = "s"
            elif base_name == "e":
                accidental_suffix = "s"
            else:
                accidental_suffix = "es"
        elif alteration == 2:
            accidental_suffix = "isis"
        elif alteration == -2:
            if base_name in ["a", "e"]:
                accidental_suffix = "ses"
            else:
                accidental_suffix = "eses"
        else:
            accidental_suffix = ""

        tonic_name = f"{base_name}{accidental_suffix}"
        mode_lily = self._get_lilypond_mode()

        try:
            return abjad.KeySignature(
                abjad.NamedPitchClass(tonic_name), abjad.Mode(mode_lily)
            )
        except:
            return None

    def _get_lilypond_mode(self) -> str:
        """Retorna el modo en formato LilyPond."""
        mode_name = self.mode.lower()
        mode_mapping = {
            "major": "major", "ionian": "major",
            "minor": "minor", "aeolian": "minor",
            "dorian": "dorian", "phrygian": "phrygian",
            "lydian": "lydian", "mixolydian": "mixolydian",
            "locrian": "locrian",
            "harmonic_minor": "minor", "melodic_minor": "minor",
            "locrian_nat6": "locrian", "ionian_aug5": "major",
            "dorian_sharp4": "dorian", "phrygian_dominant": "phrygian",
            "lydian_sharp2": "lydian", "superlocrian_bb7": "locrian",
            "dorian_flat2": "dorian", "lydian_augmented": "lydian",
            "lydian_dominant": "lydian", "mixolydian_flat6": "mixolydian",
            "locrian_nat2": "locrian", "altered": "locrian",
        }
        return mode_mapping.get(mode_name, "major")

    def get_key_signature_string(self) -> str:
        """Retorna la armadura de clave como string LilyPond."""
        tonic = self.scale_manager.get_tonic()
        base_name = tonic.step.lower()

        alteration = tonic.alter
        if alteration == 0:
            accidental_suffix = ""
        elif alteration == 1:
            accidental_suffix = "is"
        elif alteration == -1:
            if base_name == "a":
                accidental_suffix = "s"
            elif base_name == "e":
                accidental_suffix = "s"
            else:
                accidental_suffix = "es"
        else:
            accidental_suffix = ""

        tonic_name = f"{base_name}{accidental_suffix}"
        mode_lily = self._get_lilypond_mode_command()

        return f"\\key {tonic_name} {mode_lily}"

    def _get_lilypond_mode_command(self) -> str:
        """Retorna el comando de modo LilyPond (con backslash)."""
        mode_name = self.mode.lower()
        mode_mapping = {
            "major": "\\major", "ionian": "\\major",
            "minor": "\\minor", "aeolian": "\\minor",
            "dorian": "\\dorian", "phrygian": "\\phrygian",
            "lydian": "\\lydian", "mixolydian": "\\mixolydian",
            "locrian": "\\locrian",
            "harmonic_minor": "\\minor", "melodic_minor": "\\minor",
            "locrian_nat6": "\\locrian", "ionian_aug5": "\\major",
            "dorian_sharp4": "\\dorian", "phrygian_dominant": "\\phrygian",
            "lydian_sharp2": "\\lydian", "superlocrian_bb7": "\\locrian",
            "dorian_flat2": "\\dorian", "lydian_augmented": "\\lydian",
            "lydian_dominant": "\\lydian", "mixolydian_flat6": "\\mixolydian",
            "locrian_nat2": "\\locrian", "altered": "\\locrian",
        }
        return mode_mapping.get(mode_name, "\\major")

    def format_output(
        self, staff: abjad.Staff, title: Optional[str] = None, composer: Optional[str] = None
    ) -> str:
        """
        Genera el código LilyPond completo.

        Args:
            staff: Staff de Abjad con las notas
            title: Título opcional
            composer: Compositor opcional

        Returns:
            String con código LilyPond completo
        """
        key_sig_str = self.get_key_signature_string()
        time_sig = f"\\time {self.meter_tuple[0]}/{self.meter_tuple[1]}"
        clef = '\\clef "treble"'
        strict_beaming = "\\set strictBeatBeaming = ##t"

        music_code = self.to_absolute_lilypond(staff)

        output = ""

        if title or composer:
            output += "\\header {\n"
            if title:
                output += f'  title = "{title}"\n'
            if composer:
                output += f'  composer = "{composer}"\n'
            output += "}\n\n"

        output += "\\score {\n"

        lines = music_code.split("\n")
        if len(lines) > 1:
            lines[1] = (
                f"    {time_sig}\n    {key_sig_str}\n    {clef}\n    {strict_beaming}\n{lines[1]}"
            )
        output += "\n".join(lines)

        output += "\n\n  \\layout {}\n"
        output += "  \\midi {}\n"
        output += "}\n"

        return output
