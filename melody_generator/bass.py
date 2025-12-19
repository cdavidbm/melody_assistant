"""
Generación de línea de bajo armónico.
Implementa tres estilos: simple, Alberti, y walking bass diatónico.
Incluye verificación de conducción de voces.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
import random
import abjad

from .models import HarmonicFunction
from .scales import ScaleManager
from .harmony import HarmonyManager


class BassStyle(Enum):
    """Estilos de bajo disponibles."""
    SIMPLE = "simple"          # Una nota por compás (unidad de compás)
    ALBERTI = "alberti"        # Arpegio del acorde
    WALKING = "walking"        # Movimiento por grados conjuntos


@dataclass
class BassConfig:
    """Configuración para generación de bajo."""
    style: BassStyle = BassStyle.SIMPLE
    octave: int = 3                      # Octava base del bajo (C3 = Do grave)
    root_preference: float = 0.70        # Probabilidad de usar raíz del acorde
    fifth_preference: float = 0.20       # Probabilidad de usar quinta
    third_preference: float = 0.10       # Probabilidad de usar tercera
    max_leap: int = 7                    # Máximo salto en semitonos (5ta justa)
    allow_rhythm_variation: bool = False # Permitir variación rítmica ocasional
    rhythm_variation_prob: float = 0.15  # Probabilidad de variación rítmica


@dataclass
class VoiceLeadingError:
    """Representa un error de conducción de voces."""
    error_type: str           # "parallel_fifths", "parallel_octaves", "direct_fifths"
    measure_index: int        # Índice del compás donde ocurre
    description: str          # Descripción legible


# Mapeo de unidad de compás: la figura que ocupa TODO el compás
MEASURE_UNIT_DURATION: Dict[Tuple[int, int], Tuple[int, int]] = {
    # Compás: duración (numerador, denominador)
    (2, 4): (1, 2),      # Blanca
    (3, 4): (3, 4),      # Blanca con puntillo
    (4, 4): (1, 1),      # Redonda
    (5, 4): (5, 4),      # Redonda + Negra (se maneja especial con ligadura)
    (6, 4): (3, 2),      # Redonda con puntillo
    (2, 8): (1, 4),      # Negra
    (3, 8): (3, 8),      # Negra con puntillo
    (4, 8): (1, 2),      # Blanca
    (6, 8): (3, 4),      # Blanca con puntillo
    (9, 8): (9, 8),      # 3 negras con puntillo
    (12, 8): (3, 2),     # 4 negras con puntillo = redonda con puntillo
    (2, 2): (1, 1),      # Redonda (alla breve)
    (3, 2): (3, 2),      # Redonda con puntillo
}

# Unidad de pulso por denominador
BEAT_UNIT_DURATION: Dict[int, Tuple[int, int]] = {
    2: (1, 2),   # Blanca
    4: (1, 4),   # Negra
    8: (1, 8),   # Corchea
    16: (1, 16), # Semicorchea
}

# Primera división del pulso (medio pulso)
BEAT_DIVISION_DURATION: Dict[int, Tuple[int, int]] = {
    2: (1, 4),   # Media blanca = negra
    4: (1, 8),   # Media negra = corchea
    8: (1, 16),  # Media corchea = semicorchea
    16: (1, 32), # Media semicorchea = fusa
}


class VoiceLeadingChecker:
    """Verifica errores de conducción de voces entre melodía y bajo."""

    @staticmethod
    def get_interval_class(pitch1_midi: int, pitch2_midi: int) -> int:
        """
        Calcula la clase de intervalo (0-11) entre dos pitches.

        Args:
            pitch1_midi: Valor MIDI del primer pitch
            pitch2_midi: Valor MIDI del segundo pitch

        Returns:
            Clase de intervalo (0=unísono, 7=quinta, etc.)
        """
        return abs(pitch1_midi - pitch2_midi) % 12

    @staticmethod
    def check_parallel_fifths(
        melody_curr: int, bass_curr: int,
        melody_prev: int, bass_prev: int
    ) -> bool:
        """
        Verifica si hay quintas paralelas.

        Quintas paralelas: ambas voces se mueven y mantienen intervalo de 5ta.

        Returns:
            True si hay quintas paralelas (ERROR)
        """
        prev_interval = VoiceLeadingChecker.get_interval_class(melody_prev, bass_prev)
        curr_interval = VoiceLeadingChecker.get_interval_class(melody_curr, bass_curr)

        # Ambos intervalos deben ser quintas justas (7 semitonos)
        if prev_interval != 7 or curr_interval != 7:
            return False

        # Verificar que ambas voces se movieron (no es la misma nota)
        melody_moved = melody_curr != melody_prev
        bass_moved = bass_curr != bass_prev

        return melody_moved and bass_moved

    @staticmethod
    def check_parallel_octaves(
        melody_curr: int, bass_curr: int,
        melody_prev: int, bass_prev: int
    ) -> bool:
        """
        Verifica si hay octavas paralelas.

        Returns:
            True si hay octavas paralelas (ERROR)
        """
        prev_interval = VoiceLeadingChecker.get_interval_class(melody_prev, bass_prev)
        curr_interval = VoiceLeadingChecker.get_interval_class(melody_curr, bass_curr)

        # Ambos intervalos deben ser octavas/unísonos (0 semitonos mod 12)
        if prev_interval != 0 or curr_interval != 0:
            return False

        melody_moved = melody_curr != melody_prev
        bass_moved = bass_curr != bass_prev

        return melody_moved and bass_moved

    @staticmethod
    def check_direct_fifths(
        melody_curr: int, bass_curr: int,
        melody_prev: int, bass_prev: int
    ) -> bool:
        """
        Verifica si hay quintas directas (ocultas).

        Quintas directas: llegar a una 5ta con ambas voces en la misma dirección.

        Returns:
            True si hay quintas directas (advertencia, no siempre es error)
        """
        curr_interval = VoiceLeadingChecker.get_interval_class(melody_curr, bass_curr)

        # Solo verificar si llegamos a una quinta
        if curr_interval != 7:
            return False

        # Calcular direcciones
        melody_direction = melody_curr - melody_prev
        bass_direction = bass_curr - bass_prev

        # Ambas voces deben moverse en la misma dirección
        if melody_direction == 0 or bass_direction == 0:
            return False

        same_direction = (melody_direction > 0) == (bass_direction > 0)
        return same_direction


class BassGenerator:
    """
    Genera línea de bajo armónico para acompañar la melodía.

    Soporta tres estilos:
    - Simple: una nota por compás (unidad de compás)
    - Alberti: arpegio del acorde
    - Walking: movimiento diatónico por grados conjuntos
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        harmony_manager: HarmonyManager,
        meter_tuple: Tuple[int, int],
        config: Optional[BassConfig] = None,
    ):
        """
        Inicializa el generador de bajo.

        Args:
            scale_manager: Gestor de escala para obtener pitches
            harmony_manager: Gestor de armonía para progresión
            meter_tuple: Compás (numerador, denominador)
            config: Configuración del bajo
        """
        self.scale_manager = scale_manager
        self.harmony_manager = harmony_manager
        self.meter_tuple = meter_tuple
        self.config = config or BassConfig()

        # Cache de la última nota del bajo para conducción de voces
        self._last_bass_pitch: Optional[int] = None
        self._voice_leading_errors: List[VoiceLeadingError] = []

    def get_measure_unit_duration(self) -> Tuple[int, int]:
        """
        Obtiene la duración que ocupa un compás completo.

        Returns:
            Tupla (numerador, denominador) de la duración
        """
        if self.meter_tuple in MEASURE_UNIT_DURATION:
            return MEASURE_UNIT_DURATION[self.meter_tuple]

        # Fallback: calcular basado en numerador/denominador
        num, denom = self.meter_tuple
        # La duración total es num/denom redondas
        # Simplificar la fracción
        from math import gcd
        g = gcd(num, denom)
        return (num // g, denom // g)

    def get_beat_unit_duration(self) -> Tuple[int, int]:
        """Obtiene la duración de un pulso."""
        denom = self.meter_tuple[1]
        return BEAT_UNIT_DURATION.get(denom, (1, 4))

    def get_beat_division_duration(self) -> Tuple[int, int]:
        """Obtiene la duración de media pulso (primera división)."""
        denom = self.meter_tuple[1]
        return BEAT_DIVISION_DURATION.get(denom, (1, 8))

    def _select_chord_tone(
        self,
        harmonic_function: HarmonicFunction,
        prev_bass_degree: Optional[int] = None,
    ) -> int:
        """
        Selecciona un grado del acorde para el bajo.

        Preferencia: raíz > quinta > tercera
        Considera conducción de voces si hay nota previa.

        Args:
            harmonic_function: Función armónica del compás
            prev_bass_degree: Grado del bajo anterior (para voice leading)

        Returns:
            Grado de la escala seleccionado
        """
        chord_tones = harmonic_function.chord_tones
        root = chord_tones[0]
        third = chord_tones[1] if len(chord_tones) > 1 else root
        fifth = chord_tones[2] if len(chord_tones) > 2 else root

        # Si hay nota previa, preferir movimiento por grado conjunto
        if prev_bass_degree is not None:
            # Calcular distancias a cada opción
            distances = {
                root: abs(root - prev_bass_degree),
                third: abs(third - prev_bass_degree),
                fifth: abs(fifth - prev_bass_degree),
            }

            # Si alguna opción está a distancia 1 o 2, favorecerla
            close_options = [d for d, dist in distances.items() if dist <= 2]
            if close_options and random.random() < 0.4:
                return random.choice(close_options)

        # Selección por preferencias configuradas
        r = random.random()
        if r < self.config.root_preference:
            return root
        elif r < self.config.root_preference + self.config.fifth_preference:
            return fifth
        else:
            return third

    def _degree_to_pitch(self, degree: int, octave: int) -> str:
        """
        Convierte grado de escala a pitch string.

        Args:
            degree: Grado de la escala (1-7)
            octave: Octava

        Returns:
            Pitch string (ej: "c3", "g2")
        """
        return self.scale_manager.get_pitch_by_degree(degree, octave)

    def _pitch_to_abjad(self, pitch_str: str, duration: Tuple[int, int]) -> abjad.Note:
        """
        Crea una nota Abjad desde pitch string y duración.

        Args:
            pitch_str: Pitch en formato music21 (ej: "c3", "g#2", "eb3")
            duration: Duración como tupla (numerador, denominador)

        Returns:
            abjad.Note
        """
        # Convertir pitch de music21 a formato LilyPond/Abjad
        # Formato music21: "c3", "g#3", "eb2"
        # Formato LilyPond: "c", "gis'", "es,"

        from music21 import pitch as m21pitch

        p = m21pitch.Pitch(pitch_str)
        base_name = p.step.lower()

        # Alteraciones
        alteration = p.alter
        if alteration == 0:
            accidental = ""
        elif alteration == 1:
            accidental = "is"  # Sharp
        elif alteration == -1:
            if base_name in ["a", "e"]:
                accidental = "s"  # as, es
            else:
                accidental = "es"  # bes, des, ges
        elif alteration == 2:
            accidental = "isis"
        elif alteration == -2:
            if base_name in ["a", "e"]:
                accidental = "ses"
            else:
                accidental = "eses"
        else:
            accidental = ""

        # Octava (Abjad: c = C3, c' = C4, c'' = C5, c, = C2)
        octave = p.octave
        if octave == 3:
            octave_mark = ""
        elif octave < 3:
            octave_mark = "," * (3 - octave)
        else:
            octave_mark = "'" * (octave - 3)

        lily_pitch = f"{base_name}{accidental}{octave_mark}"

        # Crear string de duración para Abjad
        num, denom = duration
        if num == 1:
            dur_str = str(denom)
        elif num == 3 and denom % 2 == 0:
            # Duración con puntillo: 3/8 -> "4.", 3/4 -> "2."
            dur_str = f"{denom // 2}."
        else:
            # Para duraciones como 5/4, usar la más cercana
            dur_str = str(denom)

        # Crear nota combinando pitch y duración
        return abjad.Note(f"{lily_pitch}{dur_str}")

    def _create_tied_duration(
        self,
        pitch_str: str,
        durations: List[Tuple[int, int]]
    ) -> List[abjad.Note]:
        """
        Crea notas ligadas para duraciones que no caben en una figura.

        Usado para compases como 5/4 donde la unidad de compás
        es redonda + negra ligadas.

        Args:
            pitch_str: Pitch de la nota
            durations: Lista de duraciones a ligar

        Returns:
            Lista de notas con ligadura aplicada
        """
        notes = [self._pitch_to_abjad(pitch_str, dur) for dur in durations]

        if len(notes) > 1:
            abjad.tie(notes)

        return notes

    def generate_bass_line(
        self,
        harmonic_plan: List[HarmonicFunction],
        melody_pitches: Optional[List[int]] = None,
    ) -> abjad.Staff:
        """
        Genera la línea completa de bajo.

        Args:
            harmonic_plan: Progresión armónica (una por compás)
            melody_pitches: Lista opcional de pitches MIDI de la melodía
                           (para verificación de conducción de voces)

        Returns:
            abjad.Staff con clave de Fa
        """
        self._last_bass_pitch = None
        self._voice_leading_errors = []

        if self.config.style == BassStyle.SIMPLE:
            staff = self._generate_simple_bass(harmonic_plan, melody_pitches)
        elif self.config.style == BassStyle.ALBERTI:
            staff = self._generate_alberti_bass(harmonic_plan, melody_pitches)
        elif self.config.style == BassStyle.WALKING:
            staff = self._generate_walking_bass(harmonic_plan, melody_pitches)
        else:
            staff = self._generate_simple_bass(harmonic_plan, melody_pitches)

        # Añadir clave de Fa
        abjad.attach(abjad.Clef("bass"), abjad.get.leaf(staff, 0))

        return staff

    def _generate_simple_bass(
        self,
        harmonic_plan: List[HarmonicFunction],
        melody_pitches: Optional[List[int]] = None,
    ) -> abjad.Staff:
        """
        Genera bajo simple: una nota por compás usando unidad de compás.
        """
        notes: List[abjad.Component] = []
        prev_degree: Optional[int] = None

        for measure_idx, harmonic_func in enumerate(harmonic_plan):
            # Seleccionar grado del acorde
            degree = self._select_chord_tone(harmonic_func, prev_degree)

            # Determinar octava (ajustar para mantener rango bajo)
            octave = self.config.octave
            if degree > 5:  # Grados altos: bajar octava
                octave -= 1

            # Obtener pitch
            pitch_str = self._degree_to_pitch(degree, octave)

            # Obtener duración de unidad de compás
            duration = self.get_measure_unit_duration()

            # Manejar casos especiales (5/4, etc.) con ligaduras
            if self.meter_tuple == (5, 4):
                # Redonda + negra ligadas
                measure_notes = self._create_tied_duration(
                    pitch_str, [(1, 1), (1, 4)]
                )
                notes.extend(measure_notes)
            else:
                note = self._pitch_to_abjad(pitch_str, duration)
                notes.append(note)

            prev_degree = degree

        # Crear staff con notas
        staff = abjad.Staff(notes)

        return staff

    def _generate_alberti_bass(
        self,
        harmonic_plan: List[HarmonicFunction],
        melody_pitches: Optional[List[int]] = None,
    ) -> abjad.Staff:
        """
        Genera bajo Alberti: arpegio del acorde (raíz-quinta-tercera-quinta).

        El patrón Alberti típico en 4/4 usa corcheas:
        Do-Sol-Mi-Sol (para acorde de Do mayor)
        """
        notes: List[abjad.Component] = []
        beat_division = self.get_beat_division_duration()  # Típicamente corchea

        for measure_idx, harmonic_func in enumerate(harmonic_plan):
            chord_tones = harmonic_func.chord_tones
            root = chord_tones[0]
            third = chord_tones[1] if len(chord_tones) > 1 else root
            fifth = chord_tones[2] if len(chord_tones) > 2 else root

            # Patrón Alberti: raíz-quinta-tercera-quinta
            pattern_degrees = [root, fifth, third, fifth]

            # Calcular cuántas notas necesitamos por compás
            num_beats = self.meter_tuple[0]

            # Cada pulso tiene 2 divisiones (ej: negra = 2 corcheas)
            notes_per_measure = num_beats * 2

            # Extender patrón para llenar el compás
            extended_pattern = []
            for i in range(notes_per_measure):
                extended_pattern.append(pattern_degrees[i % len(pattern_degrees)])

            # Generar notas
            octave = self.config.octave
            for degree in extended_pattern:
                # Ajustar octava para quinta y tercera
                deg_octave = octave
                if degree == fifth and fifth < root:
                    deg_octave = octave + 1
                elif degree > 5:
                    deg_octave = octave - 1

                pitch_str = self._degree_to_pitch(degree, deg_octave)
                note = self._pitch_to_abjad(pitch_str, beat_division)
                notes.append(note)

        staff = abjad.Staff(notes)
        return staff

    def _generate_walking_bass(
        self,
        harmonic_plan: List[HarmonicFunction],
        melody_pitches: Optional[List[int]] = None,
    ) -> abjad.Staff:
        """
        Genera walking bass diatónico: movimiento por grados conjuntos.

        Conecta acordes usando notas de paso diatónicas.
        NO es jazz, es walking clásico dentro de la armonía.
        """
        notes: List[abjad.Component] = []
        beat_unit = self.get_beat_unit_duration()  # Típicamente negra

        prev_degree: Optional[int] = None

        for measure_idx, harmonic_func in enumerate(harmonic_plan):
            num_beats = self.meter_tuple[0]

            # Obtener siguiente acorde para planificar conexión
            next_func = None
            if measure_idx < len(harmonic_plan) - 1:
                next_func = harmonic_plan[measure_idx + 1]

            # Grado objetivo de este compás (raíz preferida)
            target_degree = harmonic_func.chord_tones[0]

            # Grado destino del siguiente compás
            dest_degree = next_func.chord_tones[0] if next_func else target_degree

            # Generar línea de walking para este compás
            walking_degrees = self._plan_walking_line(
                target_degree,
                dest_degree,
                num_beats,
                prev_degree,
                harmonic_func.chord_tones,
            )

            # Crear notas
            octave = self.config.octave
            for degree in walking_degrees:
                deg_octave = octave
                if degree > 5:
                    deg_octave = octave - 1

                pitch_str = self._degree_to_pitch(degree, deg_octave)
                note = self._pitch_to_abjad(pitch_str, beat_unit)
                notes.append(note)

            prev_degree = walking_degrees[-1] if walking_degrees else target_degree

        staff = abjad.Staff(notes)
        return staff

    def _plan_walking_line(
        self,
        target_degree: int,
        dest_degree: int,
        num_beats: int,
        prev_degree: Optional[int],
        chord_tones: List[int],
    ) -> List[int]:
        """
        Planifica una línea de walking bass para un compás.

        Principios:
        - Tiempo 1: nota del acorde (preferiblemente raíz)
        - Tiempos intermedios: notas de paso diatónicas
        - Último tiempo: prepara llegada al siguiente acorde

        Args:
            target_degree: Grado objetivo de este compás
            dest_degree: Grado destino del siguiente compás
            num_beats: Número de pulsos en el compás
            prev_degree: Grado del último pulso anterior
            chord_tones: Notas del acorde actual

        Returns:
            Lista de grados para cada pulso
        """
        degrees = []

        if num_beats == 1:
            degrees = [target_degree]

        elif num_beats == 2:
            # Tiempo 1: raíz, Tiempo 2: aproximación al destino
            approach = self._get_approach_note(target_degree, dest_degree)
            degrees = [target_degree, approach]

        elif num_beats == 3:
            # Tiempo 1: raíz
            # Tiempo 2: nota del acorde o paso
            # Tiempo 3: aproximación
            middle = chord_tones[2] if len(chord_tones) > 2 else target_degree
            approach = self._get_approach_note(middle, dest_degree)
            degrees = [target_degree, middle, approach]

        elif num_beats >= 4:
            # Tiempo 1: raíz
            degrees.append(target_degree)

            # Tiempos intermedios: caminar hacia el destino
            remaining = num_beats - 1
            current = target_degree

            for i in range(remaining - 1):
                # Calcular dirección
                if dest_degree > current:
                    next_deg = (current % 7) + 1
                elif dest_degree < current:
                    next_deg = ((current - 2) % 7) + 1
                else:
                    # Mismo grado: oscilar
                    next_deg = chord_tones[min(i + 1, len(chord_tones) - 1)]

                # Preferir notas del acorde en tiempos semi-fuertes
                if i == num_beats // 2 - 1 and len(chord_tones) > 2:
                    next_deg = chord_tones[2]  # quinta

                degrees.append(next_deg)
                current = next_deg

            # Último tiempo: aproximación cromática o diatónica
            approach = self._get_approach_note(current, dest_degree)
            degrees.append(approach)

        return degrees

    def _get_approach_note(self, current: int, target: int) -> int:
        """
        Obtiene nota de aproximación al grado objetivo.

        Preferencia por movimiento diatónico de grado conjunto.

        Args:
            current: Grado actual
            target: Grado objetivo

        Returns:
            Grado de aproximación
        """
        if target == current:
            return current

        # Aproximación desde abajo o arriba
        if target > current:
            # Aproximar desde un grado abajo del target
            approach = ((target - 2) % 7) + 1
        else:
            # Aproximar desde un grado arriba del target
            approach = (target % 7) + 1

        return approach

    def get_voice_leading_errors(self) -> List[VoiceLeadingError]:
        """Retorna la lista de errores de conducción de voces detectados."""
        return self._voice_leading_errors

    def verify_voice_leading(
        self,
        bass_staff: abjad.Staff,
        melody_staff: abjad.Staff,
    ) -> List[VoiceLeadingError]:
        """
        Verifica la conducción de voces entre bajo y melodía.

        Args:
            bass_staff: Staff del bajo
            melody_staff: Staff de la melodía

        Returns:
            Lista de errores detectados
        """
        errors = []

        # Extraer notas de ambos staffs
        bass_notes = [n for n in abjad.iterate.leaves(bass_staff)
                     if isinstance(n, abjad.Note)]
        melody_notes = [n for n in abjad.iterate.leaves(melody_staff)
                       if isinstance(n, abjad.Note)]

        # Necesitamos al menos 2 notas para comparar
        if len(bass_notes) < 2 or len(melody_notes) < 2:
            return errors

        # Verificar cada par de notas consecutivas
        # Simplificación: comparamos nota por nota (asume misma cantidad)
        min_len = min(len(bass_notes), len(melody_notes))

        for i in range(1, min_len):
            bass_curr = self._note_to_midi(bass_notes[i])
            bass_prev = self._note_to_midi(bass_notes[i-1])
            melody_curr = self._note_to_midi(melody_notes[i])
            melody_prev = self._note_to_midi(melody_notes[i-1])

            # Verificar quintas paralelas
            if VoiceLeadingChecker.check_parallel_fifths(
                melody_curr, bass_curr, melody_prev, bass_prev
            ):
                errors.append(VoiceLeadingError(
                    error_type="parallel_fifths",
                    measure_index=i,
                    description=f"Quintas paralelas en posición {i}"
                ))

            # Verificar octavas paralelas
            if VoiceLeadingChecker.check_parallel_octaves(
                melody_curr, bass_curr, melody_prev, bass_prev
            ):
                errors.append(VoiceLeadingError(
                    error_type="parallel_octaves",
                    measure_index=i,
                    description=f"Octavas paralelas en posición {i}"
                ))

            # Verificar quintas directas (advertencia)
            if VoiceLeadingChecker.check_direct_fifths(
                melody_curr, bass_curr, melody_prev, bass_prev
            ):
                errors.append(VoiceLeadingError(
                    error_type="direct_fifths",
                    measure_index=i,
                    description=f"Quintas directas en posición {i} (advertencia)"
                ))

        self._voice_leading_errors = errors
        return errors

    def _note_to_midi(self, note: abjad.Note) -> int:
        """Convierte nota Abjad a valor MIDI."""
        pitch = note.written_pitch
        if callable(pitch):
            pitch = pitch()
        # pitch.number is also a method in abjad
        pitch_num = pitch.number
        if callable(pitch_num):
            pitch_num = pitch_num()
        return pitch_num + 60  # C4 = 60
