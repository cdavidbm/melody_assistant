"""
Conversores de formato entre Abjad y music21.
Centraliza la lógica de conversión para reutilización.
"""

import logging
import re
from typing import Tuple

import abjad
from music21 import stream, note as m21_note, meter as m21_meter, key

logger = logging.getLogger(__name__)


class AbjadMusic21Converter:
    """
    Convierte entre formatos Abjad y music21.

    Extrae la lógica de conversión que antes estaba en MusicValidator,
    siguiendo el principio de Single Responsibility (SRP).
    """

    @staticmethod
    def lilypond_pitch_to_music21(lily_pitch: str) -> str:
        """
        Convierte un pitch en notación LilyPond a notación music21.

        Ejemplos:
            "c'" -> "C4"
            "cis''" -> "C#5"
            "bes" -> "B-3"

        Args:
            lily_pitch: Pitch en notación LilyPond (ej: "cis''")

        Returns:
            Pitch en notación music21 (ej: "C#5")
        """
        # Extraer nota base
        base_match = re.match(r"([a-g])", lily_pitch)
        if not base_match:
            return lily_pitch

        base_note = base_match.group(1).upper()

        # Manejar alteraciones
        # LilyPond soporta tanto notación holandesa (cis, bes) como inglesa (cs, bf)
        accidental_str = ""

        # Extraer parte de alteración (todo entre nota base y octava)
        alt_part = lily_pitch[1:].replace("'", "").replace(",", "")

        if "isis" in lily_pitch or "ss" in alt_part:
            accidental_str = "##"
        elif "is" in lily_pitch:
            # Notación holandesa: cis, dis, fis, gis, ais
            accidental_str = "#"
        elif alt_part == "s" and base_note not in ["A", "E"]:
            # Notación inglesa: cs, ds, fs, gs (pero no es ni as que son bemoles)
            accidental_str = "#"
        elif "eses" in lily_pitch or "asas" in lily_pitch or "ff" in alt_part:
            accidental_str = "--"
        elif alt_part == "f" or (base_note == "B" and alt_part == ""):
            # bf o b solo (si b está sin alteración, verificar contexto)
            if alt_part == "f":
                accidental_str = "-"
        elif "es" in lily_pitch:
            # Notación holandesa: es, bes, des, ges, aes
            accidental_str = "-"
        elif alt_part == "s" and base_note in ["A", "E"]:
            # as y es son bemoles en notación holandesa
            accidental_str = "-"

        # Calcular octava (c, = C2; c = C3; c' = C4; c'' = C5)
        num_apostrophes = lily_pitch.count("'")
        num_commas = lily_pitch.count(",")
        octave = 3 + num_apostrophes - num_commas

        return f"{base_note}{accidental_str}{octave}"

    @staticmethod
    def music21_pitch_to_lilypond(m21_pitch: str) -> str:
        """
        Convierte un pitch en notación music21 a notación LilyPond.

        Ejemplos:
            "C4" -> "c'"
            "C#5" -> "cis''"
            "B-3" -> "bes"

        Args:
            m21_pitch: Pitch en notación music21 (ej: "C#5")

        Returns:
            Pitch en notación LilyPond (ej: "cis''")
        """
        # Parsear con regex
        match = re.match(r"([A-Ga-g])([#-]*)(\d+)", m21_pitch)
        if not match:
            return m21_pitch

        note_name = match.group(1).lower()
        accidentals = match.group(2)
        octave = int(match.group(3))

        # Convertir alteraciones
        lily_accidental = ""
        if accidentals == "#":
            lily_accidental = "is"
        elif accidentals == "##":
            lily_accidental = "isis"
        elif accidentals == "-":
            lily_accidental = "es"
        elif accidentals == "--":
            lily_accidental = "eses"

        # Calcular marcadores de octava
        # C3 = c (sin marcador), C4 = c', C5 = c''
        octave_markers = ""
        if octave > 3:
            octave_markers = "'" * (octave - 3)
        elif octave < 3:
            octave_markers = "," * (3 - octave)

        return f"{note_name}{lily_accidental}{octave_markers}"

    @classmethod
    def abjad_staff_to_music21_score(
        cls,
        staff: abjad.Staff,
        key_name: str,
        mode: str,
        meter_tuple: Tuple[int, int],
    ) -> stream.Score:
        """
        Convierte un Staff de Abjad a un Score de music21.

        Args:
            staff: Staff de Abjad a convertir
            key_name: Nombre de la tonalidad (ej: "C", "D", "Eb")
            mode: Modo musical (ej: "major", "minor")
            meter_tuple: Compás como tupla (numerador, denominador)

        Returns:
            Score de music21
        """
        score = stream.Score()
        part = stream.Part()

        # Añadir time signature
        ts_str = f"{meter_tuple[0]}/{meter_tuple[1]}"
        ts = m21_meter.TimeSignature(ts_str)
        part.insert(0, ts)

        # Añadir key signature
        try:
            ks = key.Key(key_name, mode)
            part.insert(0, ks)
        except Exception as e:
            logger.warning(f"No se pudo crear key signature para {key_name} {mode}: {e}")

        # Calcular duración esperada por compás
        expected_measure_duration = meter_tuple[0] / meter_tuple[1] * 4.0

        # Iterar sobre las hojas del staff
        current_measure = stream.Measure(number=1)
        measure_duration = 0.0
        measure_num = 1

        try:
            for leaf in abjad.iterate.leaves(staff):
                # Obtener duración en quarter notes
                duration = abjad.get.duration(leaf)
                duration_quarters = float(duration) * 4.0

                # Verificar tipo de hoja
                if isinstance(leaf, abjad.Note):
                    lily_str = abjad.lilypond(leaf)

                    # Extraer pitch
                    match = re.match(r"([a-g][',is#esf]*)", lily_str)
                    if match:
                        pitch_lily = match.group(1)
                        pitch_str = cls.lilypond_pitch_to_music21(pitch_lily)

                        n = m21_note.Note(pitch_str)
                        n.quarterLength = duration_quarters
                        current_measure.append(n)

                elif isinstance(leaf, abjad.Rest):
                    r = m21_note.Rest()
                    r.quarterLength = duration_quarters
                    current_measure.append(r)

                measure_duration += duration_quarters

                # Verificar si completamos un compás
                if abs(measure_duration - expected_measure_duration) < 0.01:
                    if len(current_measure.notesAndRests) > 0:
                        part.append(current_measure)
                    measure_num += 1
                    current_measure = stream.Measure(number=measure_num)
                    measure_duration = 0.0

        except Exception as e:
            logger.error(f"Error convirtiendo staff de Abjad a music21: {e}")

        # Añadir último compás si tiene contenido
        if len(current_measure.notesAndRests) > 0:
            existing_measures = list(part.getElementsByClass(stream.Measure))
            if not existing_measures or current_measure.id != existing_measures[-1].id:
                part.append(current_measure)

        score.insert(0, part)
        return score

    @staticmethod
    def get_duration_in_quarter_notes(duration_tuple: Tuple[int, int]) -> float:
        """
        Convierte una tupla de duración a quarter notes.

        Args:
            duration_tuple: Tupla (numerador, denominador) ej: (1, 4) = negra

        Returns:
            Duración en quarter notes
        """
        num, denom = duration_tuple
        return (num / denom) * 4.0

    @staticmethod
    def quarter_notes_to_duration_tuple(ql: float) -> Tuple[int, int]:
        """
        Convierte quarter notes a tupla de duración.

        Args:
            ql: Duración en quarter notes

        Returns:
            Tupla (numerador, denominador)
        """
        from fractions import Fraction

        frac = Fraction(ql).limit_denominator(32)

        # ql=1.0 es negra (denominador 4)
        numerator = frac.numerator
        denominator = 4 * frac.denominator

        from math import gcd
        g = gcd(numerator, denominator)
        numerator //= g
        denominator //= g

        return (numerator, denominator)
