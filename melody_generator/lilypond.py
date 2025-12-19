"""
Formateo de salida LilyPond.
Convierte estructuras musicales a código LilyPond compatible.
"""

from typing import Tuple, Optional

import abjad
from music21 import pitch, key

from .scales import ScaleManager
from .models import ImpulseType


class LilyPondFormatter:
    """
    Formatea la salida musical a código LilyPond.
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        mode: str,
        meter_tuple: Tuple[int, int],
        impulse_type: ImpulseType = ImpulseType.TETIC,
        anacrusis_duration: Optional[Tuple[int, int]] = None,
    ):
        """
        Inicializa el formateador.

        Args:
            scale_manager: Gestor de escalas
            mode: Modo musical
            meter_tuple: Compás (numerador, denominador)
            impulse_type: Tipo de inicio (TETIC, ANACROUSTIC, ACEPHALOUS)
            anacrusis_duration: Duración de la anacrusa (num, denom)
        """
        self.scale_manager = scale_manager
        self.mode = mode
        self.meter_tuple = meter_tuple
        self.impulse_type = impulse_type
        self.anacrusis_duration = anacrusis_duration or self._default_anacrusis()

    def _default_anacrusis(self) -> Tuple[int, int]:
        """Calcula duración por defecto de anacrusa (un pulso)."""
        num, denom = self.meter_tuple
        # Compases compuestos
        if num in [6, 9, 12] and denom == 8:
            return (1, 8)
        return (1, denom)

    def get_partial_command(self) -> str:
        """
        Genera el comando \\partial para anacrusis en LilyPond.

        Returns:
            String con comando \\partial (ej: "\\partial 4" para una negra)
            o string vacío si no hay anacrusis
        """
        if self.impulse_type != ImpulseType.ANACROUSTIC:
            return ""

        num, denom = self.anacrusis_duration

        if num == 1:
            return f"\\partial {denom}"
        elif num == 3:
            # Duración con puntillo
            base_map = {8: 4, 16: 8, 4: 2, 32: 16, 2: 1}
            base = base_map.get(denom, denom)
            return f"\\partial {base}."
        else:
            # Para otros casos, usar fracción
            return f"\\partial {denom}*{num}"

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

        Incluye dinámicas, articulaciones, slurs y otras expresiones.

        Returns:
            String con código LilyPond usando notación absoluta
        """
        leaves = list(abjad.select.leaves(staff))

        if not leaves:
            return "{ }"

        lily_elements = []

        for i, leaf in enumerate(leaves):
            note_str = ""

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

                note_str = f"{pitch_str}{lily_duration}"

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

                note_str = f"r{lily_duration}"

            # Procesar indicadores (expresiones) adjuntos a esta nota
            indicators = abjad.get.indicators(leaf)
            articulation_str = ""
            dynamic_str = ""
            hairpin_str = ""
            slur_start = ""
            slur_end = ""
            barline_str = ""

            ornament_str = ""

            for indicator in indicators:
                # Dinámicas
                if isinstance(indicator, abjad.Dynamic):
                    dynamic_str = f"\\{indicator.name}"
                # Hairpins (crescendo/diminuendo)
                elif isinstance(indicator, abjad.StartHairpin):
                    if indicator.shape == "<":
                        hairpin_str = "\\<"
                    elif indicator.shape == ">":
                        hairpin_str = "\\>"
                elif isinstance(indicator, abjad.StopHairpin):
                    hairpin_str = "\\!"
                # Articulaciones
                elif isinstance(indicator, abjad.Articulation):
                    art_name = indicator.name
                    if art_name == "staccato":
                        articulation_str = "-."
                    elif art_name == "staccatissimo":
                        articulation_str = "-!"
                    elif art_name == "tenuto":
                        articulation_str = "--"
                    elif art_name == "accent":
                        articulation_str = "->"
                    elif art_name == "marcato":
                        articulation_str = "-^"
                    else:
                        articulation_str = f"-\\{art_name}"
                # Fermata
                elif isinstance(indicator, abjad.Fermata):
                    articulation_str = "\\fermata"
                # Slurs
                elif isinstance(indicator, abjad.StartSlur):
                    slur_start = "("
                elif isinstance(indicator, abjad.StopSlur):
                    slur_end = ")"
                # Barlines
                elif isinstance(indicator, abjad.BarLine):
                    if indicator.abbreviation == "|.":
                        barline_str = '\\bar "|."'
                    else:
                        barline_str = "|"
                # Ornamentos (LilyPondLiteral)
                elif isinstance(indicator, abjad.LilyPondLiteral):
                    literal_arg = indicator.argument
                    # Filtrar ornamentos conocidos
                    if literal_arg in ["\\trill", "\\mordent", "\\prall", "\\turn"]:
                        ornament_str = literal_arg

            # Construir el elemento completo
            # Orden: nota + ornamento + articulacion + dinamica + hairpin + slur_end + slur_start + barline
            full_element = note_str
            if ornament_str:
                full_element += ornament_str
            if articulation_str:
                full_element += articulation_str
            if dynamic_str:
                full_element += " " + dynamic_str
            if hairpin_str:
                full_element += " " + hairpin_str
            if slur_end:
                full_element += slur_end
            if slur_start:
                full_element += slur_start

            if full_element:
                lily_elements.append(full_element)

            if barline_str:
                lily_elements.append(barline_str)

        output_lines = []
        current_line = []
        elements_per_line = 4  # Menos elementos por linea para mayor legibilidad

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

    def is_advanced_mode(self) -> bool:
        """
        Verifica si el modo actual es un modo avanzado que LilyPond
        no soporta nativamente.

        Los modos avanzados incluyen:
        - Modos de menor armónica (locrian_nat6, ionian_aug5, etc.)
        - Modos de menor melódica (dorian_flat2, lydian_augmented, etc.)
        - harmonic_minor, melodic_minor (armadura aproximada)
        """
        advanced_modes = {
            "harmonic_minor", "melodic_minor",
            "locrian_nat6", "ionian_aug5", "dorian_sharp4",
            "phrygian_dominant", "lydian_sharp2", "superlocrian_bb7",
            "dorian_flat2", "lydian_augmented", "lydian_dominant",
            "mixolydian_flat6", "locrian_nat2", "altered",
        }
        return self.mode.lower() in advanced_modes

    def get_mode_annotation(self) -> str:
        """
        Genera una anotación textual para modos avanzados.

        Returns:
            String con anotación de modo, o vacío si es modo estándar
        """
        if not self.is_advanced_mode():
            return ""

        mode_display_names = {
            "harmonic_minor": "Harmonic Minor",
            "melodic_minor": "Melodic Minor",
            "locrian_nat6": "Locrian ♮6",
            "ionian_aug5": "Ionian ♯5",
            "dorian_sharp4": "Dorian ♯4",
            "phrygian_dominant": "Phrygian Dominant",
            "lydian_sharp2": "Lydian ♯2",
            "superlocrian_bb7": "Superlocrian ♭♭7",
            "dorian_flat2": "Dorian ♭2",
            "lydian_augmented": "Lydian Augmented",
            "lydian_dominant": "Lydian Dominant",
            "mixolydian_flat6": "Mixolydian ♭6",
            "locrian_nat2": "Locrian ♮2",
            "altered": "Altered (Super Locrian)",
        }
        display_name = mode_display_names.get(self.mode.lower(), self.mode)
        return f'% Mode: {display_name} (key signature is approximate)'

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

        Nota: Para inicio anacrúsico, incluye automáticamente \\partial.
        """
        key_sig_str = self.get_key_signature_string()
        time_sig = f"\\time {self.meter_tuple[0]}/{self.meter_tuple[1]}"
        clef = '\\clef "treble"'
        strict_beaming = "\\set strictBeatBeaming = ##t"

        # Comando \partial para anacrusis
        partial_cmd = self.get_partial_command()

        music_code = self.to_absolute_lilypond(staff)

        output = ""

        # Anotación para modos avanzados (key signature aproximada)
        mode_annotation = self.get_mode_annotation()
        if mode_annotation:
            output += f"{mode_annotation}\n\n"

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
            # Construir la línea de indicaciones iniciales
            initial_indications = f"    {time_sig}\n    {key_sig_str}\n    {clef}\n    {strict_beaming}"

            # Añadir \partial si hay anacrusis
            if partial_cmd:
                initial_indications += f"\n    {partial_cmd}"

            lines[1] = f"{initial_indications}\n{lines[1]}"

        output += "\n".join(lines)

        output += "\n\n  \\layout {}\n"
        output += "  \\midi {}\n"
        output += "}\n"

        return output

    def format_output_polyphonic(
        self,
        melody_staff: abjad.Staff,
        bass_staff: abjad.Staff,
        title: Optional[str] = None,
        composer: Optional[str] = None,
    ) -> str:
        """
        Genera código LilyPond para melodía + bajo (dos pentagramas).

        Crea un PianoStaff con clave de Sol arriba y clave de Fa abajo.

        Args:
            melody_staff: Staff con la melodía (clave de Sol)
            bass_staff: Staff con el bajo (clave de Fa)
            title: Título opcional
            composer: Compositor opcional

        Returns:
            String con código LilyPond completo para dos pentagramas
        """
        key_sig_str = self.get_key_signature_string()
        time_sig = f"\\time {self.meter_tuple[0]}/{self.meter_tuple[1]}"
        strict_beaming = "\\set strictBeatBeaming = ##t"

        # Comando \partial para anacrusis
        partial_cmd = self.get_partial_command()

        # Convertir staffs a código LilyPond
        melody_code = self.to_absolute_lilypond(melody_staff)
        bass_code = self.to_absolute_lilypond(bass_staff)

        output = ""

        # Anotación para modos avanzados
        mode_annotation = self.get_mode_annotation()
        if mode_annotation:
            output += f"{mode_annotation}\n\n"

        if title or composer:
            output += "\\header {\n"
            if title:
                output += f'  title = "{title}"\n'
            if composer:
                output += f'  composer = "{composer}"\n'
            output += "}\n\n"

        output += "\\score {\n"
        output += "  \\new PianoStaff <<\n"

        # Staff superior (melodía, clave de Sol)
        output += "    \\new Staff {\n"
        output += f"      {time_sig}\n"
        output += f"      {key_sig_str}\n"
        output += '      \\clef "treble"\n'
        output += f"      {strict_beaming}\n"
        if partial_cmd:
            output += f"      {partial_cmd}\n"

        # Insertar contenido de la melodía
        melody_lines = melody_code.split("\n")
        for line in melody_lines:
            if line.strip() and line.strip() not in ["{", "}"]:
                output += f"      {line.strip()}\n"
            elif line.strip() == "}":
                pass  # No cerrar aquí todavía

        output += "    }\n"

        # Staff inferior (bajo, clave de Fa)
        output += "    \\new Staff {\n"
        output += f"      {time_sig}\n"
        output += f"      {key_sig_str}\n"
        output += '      \\clef "bass"\n'
        output += f"      {strict_beaming}\n"
        if partial_cmd:
            output += f"      {partial_cmd}\n"

        # Insertar contenido del bajo
        bass_lines = bass_code.split("\n")
        for line in bass_lines:
            if line.strip() and line.strip() not in ["{", "}"]:
                output += f"      {line.strip()}\n"
            elif line.strip() == "}":
                pass

        output += "    }\n"

        output += "  >>\n"  # Cerrar PianoStaff

        output += "\n  \\layout {\n"
        output += "    \\context {\n"
        output += "      \\PianoStaff\n"
        output += "      \\consists \"Span_bar_engraver\"\n"
        output += "    }\n"
        output += "  }\n"
        output += "  \\midi {}\n"
        output += "}\n"

        return output

    def staff_to_lily_content(self, staff: abjad.Staff) -> str:
        """
        Convierte un Staff a contenido LilyPond sin llaves externas.

        Útil para combinar múltiples staffs en estructuras más complejas.

        Args:
            staff: Staff de Abjad

        Returns:
            String con las notas en formato LilyPond (sin {})
        """
        full_code = self.to_absolute_lilypond(staff)

        # Remover llaves externas
        lines = full_code.split("\n")
        content_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and stripped not in ["{", "}"]:
                content_lines.append(stripped)

        return " ".join(content_lines)
