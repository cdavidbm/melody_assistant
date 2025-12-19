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

from .models import HarmonicFunction, ImpulseType
from .scales import ScaleManager
from .harmony import HarmonyManager


class BassStyle(Enum):
    """Estilos de bajo disponibles."""
    SIMPLE = "simple"          # Una nota por compás (unidad de compás)
    ALBERTI = "alberti"        # Arpegio del acorde
    WALKING = "walking"        # Movimiento por grados conjuntos
    CONTRAPUNTO = "contrapunto"  # Bajo melódico contrapuntístico


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

    # Control de rango/ámbito (MIDI values)
    min_pitch: int = 36                  # C2 - límite inferior del bajo
    max_pitch: int = 60                  # C4 - límite superior del bajo
    preferred_min: int = 40              # E2 - rango preferido inferior
    preferred_max: int = 55              # G3 - rango preferido superior

    # Expresión musical
    use_dynamics: bool = True            # Aplicar dinámicas
    use_articulations: bool = True       # Aplicar articulaciones
    use_slurs: bool = True               # Aplicar ligaduras de fraseo
    dynamic_offset: int = -1             # Offset dinámico vs melodía (-1 = un nivel más suave)
    articulation_style: str = "sustained"  # "sustained", "detached", "mixed"

    # Configuración para bajo CONTRAPUNTO (melódico)
    melodic_activity: float = 0.6        # Actividad melódica (0.0=estático, 1.0=muy activo)
    stepwise_preference: float = 0.75    # Preferencia por movimiento por grado conjunto
    contrary_motion_pref: float = 0.7    # Preferencia por movimiento contrario a melodía
    passing_tone_ratio: float = 0.15     # Ratio de notas de paso permitidas
    consonance_strictness: float = 0.90  # Estrictez armónica (tiempos fuertes = acorde)


@dataclass
class BassMotif:
    """
    Representa un motivo melódico-rítmico para el bajo.

    El bajo motívico requiere patrones estables que refuercen la armonía.
    """
    intervals: List[int]           # Intervalos en grados (ej: [0, 2, -1, 0] = raíz-3ra-2da-raíz)
    durations: List[Tuple[int, int]]  # Duraciones (ej: [(1,4), (1,8), (1,8), (1,4)])
    is_structural: List[bool]      # True si es nota estructural (del acorde)
    name: str = "bass_motif"       # Nombre identificador

    @property
    def length(self) -> int:
        """Número de notas en el motivo."""
        return len(self.intervals)

    def get_total_duration(self) -> float:
        """Calcula duración total del motivo en negras."""
        total = 0.0
        for num, denom in self.durations:
            total += (num / denom) * 4  # Convertir a negras (1/4 = 1)
        return total


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


# =============================================================================
# MOTIVOS PREDEFINIDOS PARA BAJO (Patrones estables y armónicamente sólidos)
# =============================================================================

# Motivos para 4/4 (estables, basados en notas del acorde)
BASS_MOTIF_PATTERNS_4_4: List[BassMotif] = [
    # Motivo 1: Bajo ostinato simple (raíz-quinta-raíz-quinta)
    BassMotif(
        intervals=[0, 4, 0, 4],              # Raíz, quinta, raíz, quinta
        durations=[(1, 4), (1, 4), (1, 4), (1, 4)],
        is_structural=[True, True, True, True],
        name="ostinato_simple",
    ),
    # Motivo 2: Bajo descendente con bordadura (raíz-7-raíz-quinta)
    BassMotif(
        intervals=[0, -1, 0, 4],             # Raíz, 7mo grado, raíz, quinta
        durations=[(1, 4), (1, 8), (1, 8), (1, 2)],
        is_structural=[True, False, True, True],  # 7mo es nota de paso
        name="desc_bordadura",
    ),
    # Motivo 3: Arpegio descendente (raíz-quinta-tercera-raíz)
    BassMotif(
        intervals=[0, 4, 2, 0],              # Raíz, quinta, tercera, raíz (octava baja)
        durations=[(1, 2), (1, 4), (1, 8), (1, 8)],
        is_structural=[True, True, True, True],
        name="arp_descendente",
    ),
    # Motivo 4: Pedal con movimiento (raíz-raíz-quinta-raíz)
    BassMotif(
        intervals=[0, 0, 4, 0],
        durations=[(1, 2), (1, 4), (1, 8), (1, 8)],
        is_structural=[True, True, True, True],
        name="pedal_movimiento",
    ),
    # Motivo 5: Salto de octava (raíz grave-raíz aguda-quinta-raíz)
    BassMotif(
        intervals=[0, 7, 4, 0],              # Grado escala: 0=raíz, 7=octava
        durations=[(1, 4), (1, 4), (1, 4), (1, 4)],
        is_structural=[True, True, True, True],
        name="salto_octava",
    ),
]

# Motivos para 3/4 (estables para compás ternario)
BASS_MOTIF_PATTERNS_3_4: List[BassMotif] = [
    # Motivo 1: Vals simple (raíz-quinta-quinta)
    BassMotif(
        intervals=[0, 4, 4],
        durations=[(1, 4), (1, 4), (1, 4)],
        is_structural=[True, True, True],
        name="vals_simple",
    ),
    # Motivo 2: Vals con tercera (raíz-tercera-quinta)
    BassMotif(
        intervals=[0, 2, 4],
        durations=[(1, 2), (1, 8), (1, 8)],
        is_structural=[True, True, True],
        name="vals_tercera",
    ),
    # Motivo 3: Pedal (raíz sostenida)
    BassMotif(
        intervals=[0],
        durations=[(3, 4)],                  # Blanca con puntillo
        is_structural=[True],
        name="pedal_3_4",
    ),
]

# Motivos para 2/4 (estables para compás binario corto)
BASS_MOTIF_PATTERNS_2_4: List[BassMotif] = [
    # Motivo 1: Bajo binario simple
    BassMotif(
        intervals=[0, 4],
        durations=[(1, 4), (1, 4)],
        is_structural=[True, True],
        name="binario_simple",
    ),
    # Motivo 2: Bajo binario con subdivisión
    BassMotif(
        intervals=[0, 0, 4],
        durations=[(1, 8), (1, 8), (1, 4)],
        is_structural=[True, True, True],
        name="binario_subdivision",
    ),
]

# Motivos para 6/8 (compás compuesto)
BASS_MOTIF_PATTERNS_6_8: List[BassMotif] = [
    # Motivo 1: Siciliana (raíz-quinta-raíz)
    BassMotif(
        intervals=[0, 4, 0],
        durations=[(3, 8), (3, 8)],          # Dos negras con puntillo
        is_structural=[True, True],
        name="siciliana",
    ),
    # Motivo 2: Barcarola
    BassMotif(
        intervals=[0, 2, 4],
        durations=[(1, 8), (1, 8), (1, 8)],
        is_structural=[True, True, True],
        name="barcarola",
    ),
]

# Mapeo de compás a patrones disponibles
BASS_MOTIF_BY_METER: Dict[Tuple[int, int], List[BassMotif]] = {
    (4, 4): BASS_MOTIF_PATTERNS_4_4,
    (3, 4): BASS_MOTIF_PATTERNS_3_4,
    (2, 4): BASS_MOTIF_PATTERNS_2_4,
    (6, 8): BASS_MOTIF_PATTERNS_6_8,
    (2, 2): BASS_MOTIF_PATTERNS_2_4,  # Alla breve usa patrones similares
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
        impulse_type: ImpulseType = ImpulseType.TETIC,
        anacrusis_duration: Optional[Tuple[int, int]] = None,
    ):
        """
        Inicializa el generador de bajo.

        Args:
            scale_manager: Gestor de escala para obtener pitches
            harmony_manager: Gestor de armonía para progresión
            meter_tuple: Compás (numerador, denominador)
            config: Configuración del bajo
            impulse_type: Tipo de inicio (TETIC, ANACROUSTIC, ACEPHALOUS)
            anacrusis_duration: Duración de la anacrusis (si aplica)
        """
        self.scale_manager = scale_manager
        self.harmony_manager = harmony_manager
        self.meter_tuple = meter_tuple
        self.config = config or BassConfig()
        self.impulse_type = impulse_type
        self.anacrusis_duration = anacrusis_duration or self._default_anacrusis()

        # Cache de la última nota del bajo para conducción de voces
        self._last_bass_pitch: Optional[int] = None
        self._voice_leading_errors: List[VoiceLeadingError] = []

    def _default_anacrusis(self) -> Tuple[int, int]:
        """Calcula duración por defecto de anacrusis (un pulso)."""
        num, denom = self.meter_tuple
        # Compases compuestos
        if num in [6, 9, 12] and denom == 8:
            return (1, 8)
        return (1, denom)

    def _create_anacrusis_rest(self) -> abjad.Rest:
        """
        Crea un silencio para la anacrusis del bajo.

        Cuando la melodía comienza con anacrusis, el bajo NO toca
        durante esa anacrusis - comienza en el siguiente compás.

        Returns:
            abjad.Rest con la duración de la anacrusis
        """
        num, denom = self.anacrusis_duration
        if num == 1:
            dur_str = str(denom)
        elif num == 3 and denom % 2 == 0:
            dur_str = f"{denom // 2}."
        else:
            dur_str = str(denom)

        # abjad.Rest necesita el prefijo "r" para la notación
        return abjad.Rest(f"r{dur_str}")

    def _get_tonic_degree(self) -> int:
        """
        Retorna el grado 1 (tónica) para la primera nota del bajo.

        La primera nota del bajo SIEMPRE debe ser la tónica,
        independientemente de la progresión armónica.
        """
        return 1

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
        # Convertir pitch de music21 a formato Abjad (notación inglesa)
        # Formato music21: "c3", "g#3", "eb2"
        # Formato Abjad: "c", "gs'", "ef," (inglés: s=sharp, f=flat)

        from music21 import pitch as m21pitch

        p = m21pitch.Pitch(pitch_str)
        base_name = p.step.lower()

        # Alteraciones (usar notación Inglesa para Abjad: s=sharp, f=flat)
        alteration = p.alter
        if alteration == 0:
            accidental = ""
        elif alteration == 1:
            accidental = "s"  # Sharp (fs, cs, gs)
        elif alteration == -1:
            accidental = "f"  # Flat (bf, ef, af)
        elif alteration == 2:
            accidental = "ss"  # Double sharp
        elif alteration == -2:
            accidental = "ff"  # Double flat
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

        Reglas de inicio:
        - ANACROUSTIC: El bajo comienza con silencio (no toca durante anacrusis)
        - TETIC/ACEPHALOUS: El bajo comienza normalmente en el primer pulso
        - Primera nota: SIEMPRE es la tónica del primer acorde (obligatorio)

        Args:
            harmonic_plan: Progresión armónica (una por compás)
            melody_pitches: Lista opcional de pitches MIDI de la melodía
                           (para verificación de conducción de voces)

        Returns:
            abjad.Staff con clave de Fa
        """
        self._last_bass_pitch = None
        self._voice_leading_errors = []
        self._current_num_measures = len(harmonic_plan)  # Para cálculo de consonancias

        # Generar según estilo
        if self.config.style == BassStyle.SIMPLE:
            staff = self._generate_simple_bass(harmonic_plan, melody_pitches)
        elif self.config.style == BassStyle.ALBERTI:
            staff = self._generate_alberti_bass(harmonic_plan, melody_pitches)
        elif self.config.style == BassStyle.WALKING:
            staff = self._generate_walking_bass(harmonic_plan, melody_pitches)
        elif self.config.style == BassStyle.CONTRAPUNTO:
            staff = self._generate_contrapunto_bass(harmonic_plan, melody_pitches)
        else:
            staff = self._generate_simple_bass(harmonic_plan, melody_pitches)

        # Si es anacrúsico, insertar silencio al inicio
        if self.impulse_type == ImpulseType.ANACROUSTIC:
            anacrusis_rest = self._create_anacrusis_rest()
            # Insertar silencio al principio del staff
            staff.insert(0, anacrusis_rest)

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

        Primera nota: SIEMPRE tónica (grado 1), obligatorio.
        """
        notes: List[abjad.Component] = []
        prev_degree: Optional[int] = None

        for measure_idx, harmonic_func in enumerate(harmonic_plan):
            # Primera nota SIEMPRE es la tónica (obligatorio)
            if measure_idx == 0:
                degree = self._get_tonic_degree()
            else:
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

        Primera nota: SIEMPRE tónica (grado 1), obligatorio.
        """
        notes: List[abjad.Component] = []
        beat_division = self.get_beat_division_duration()  # Típicamente corchea

        for measure_idx, harmonic_func in enumerate(harmonic_plan):
            chord_tones = harmonic_func.chord_tones
            root = chord_tones[0]
            third = chord_tones[1] if len(chord_tones) > 1 else root
            fifth = chord_tones[2] if len(chord_tones) > 2 else root

            # Primera nota del bajo SIEMPRE es la tónica (obligatorio)
            if measure_idx == 0:
                root = self._get_tonic_degree()

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

        Primera nota: SIEMPRE tónica (grado 1), obligatorio.
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

            # Primera nota del bajo SIEMPRE es la tónica (obligatorio)
            if measure_idx == 0:
                target_degree = self._get_tonic_degree()
            else:
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

            # Crear notas con verificación de consonancias
            octave = self.config.octave
            for note_idx, degree in enumerate(walking_degrees):
                deg_octave = octave
                if degree > 5:
                    deg_octave = octave - 1

                # VERIFICAR Y CORREGIR CONSONANCIA con la melodía
                is_strong_beat = (note_idx == 0)  # Tiempo 1 es fuerte
                degree = self._verify_and_fix_consonance(
                    bass_degree=degree,
                    chord_tones=harmonic_func.chord_tones,
                    melody_pitches=melody_pitches,
                    measure_idx=measure_idx,
                    note_idx=note_idx,
                    is_strong_beat=is_strong_beat,
                    octave=deg_octave,
                )

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

    # =========================================================================
    # GENERACIÓN DE BAJO CONTRAPUNTÍSTICO (MELÓDICO)
    # =========================================================================

    # Patrones rítmicos para bajo contrapuntístico (más variados que walking)
    CONTRAPUNTO_RHYTHMS_4_4 = [
        # Patrón 1: Síncopa elegante
        [(1, 4), (1, 8), (1, 8), (1, 4), (1, 4)],
        # Patrón 2: Corcheas con reposo
        [(1, 8), (1, 8), (1, 8), (1, 8), (1, 2)],
        # Patrón 3: Anacrúsico interno
        [(1, 4), (1, 4), (1, 8), (1, 8), (1, 4)],
        # Patrón 4: Negra con puntillo
        [(3, 8), (1, 8), (1, 4), (1, 4)],
        # Patrón 5: Escala rápida
        [(1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 8), (1, 4)],
        # Patrón 6: Largo-corto-corto
        [(1, 2), (1, 8), (1, 8), (1, 8), (1, 8)],
    ]

    CONTRAPUNTO_RHYTHMS_3_4 = [
        # Patrón 1: Vals melódico
        [(1, 4), (1, 8), (1, 8), (1, 4)],
        # Patrón 2: Síncopa
        [(1, 8), (1, 4), (1, 8), (1, 4)],
        # Patrón 3: Fluido
        [(1, 8), (1, 8), (1, 8), (1, 8), (1, 4)],
    ]

    def _generate_contrapunto_bass(
        self,
        harmonic_plan: List[HarmonicFunction],
        melody_pitches: Optional[List[int]] = None,
    ) -> abjad.Staff:
        """
        Genera bajo contrapuntístico con línea melódica verdaderamente independiente.

        DIFERENCIAS CON WALKING BASS:
        - Ritmos variados (no solo negras): síncopas, corcheas, puntillos
        - Saltos melódicos frecuentes (3ras, 4tas, 5tas, 6tas)
        - Contorno propio con arco y clímax
        - Figuras melódicas: escalas, arpegios rotos, bordaduras
        - Mayor porcentaje de notas de paso (25-30%)
        - Independencia rítmica de la melodía

        Args:
            harmonic_plan: Progresión armónica (una por compás)
            melody_pitches: Lista opcional de pitches MIDI de la melodía

        Returns:
            abjad.Staff con el bajo contrapuntístico
        """
        notes: List[abjad.Component] = []
        num_measures = len(harmonic_plan)

        # Planificar contorno global del bajo (arco melódico propio)
        bass_contour = self._plan_bass_contour(num_measures)

        # Estado melódico
        prev_degree: Optional[int] = None
        current_octave = self.config.octave

        for measure_idx, harmonic_func in enumerate(harmonic_plan):
            chord_tones = harmonic_func.chord_tones

            # Primera nota SIEMPRE es la tónica (obligatorio)
            if measure_idx == 0:
                target_degree = self._get_tonic_degree()
            else:
                target_degree = chord_tones[0]

            # Obtener el contorno objetivo para este compás
            contour_target = bass_contour[measure_idx]

            # Seleccionar patrón rítmico variado
            rhythm_pattern = self._select_contrapunto_rhythm()

            # Generar figura melódica para este compás
            measure_notes = self._generate_contrapunto_figure(
                target_degree=target_degree,
                chord_tones=chord_tones,
                rhythm_pattern=rhythm_pattern,
                prev_degree=prev_degree,
                contour_direction=contour_target,
                melody_pitches=melody_pitches,
                measure_idx=measure_idx,
                is_climax=(measure_idx == num_measures // 2),
                is_cadence=(measure_idx >= num_measures - 2),
            )

            notes.extend(measure_notes)

            # Actualizar estado
            if measure_notes:
                last_note = measure_notes[-1]
                if isinstance(last_note, abjad.Note):
                    pitch = last_note.written_pitch
                    if callable(pitch):
                        pitch = pitch()
                    # Extraer grado aproximado
                    prev_degree = target_degree

        staff = abjad.Staff(notes)
        return staff

    def _plan_bass_contour(self, num_measures: int) -> List[int]:
        """
        Planifica el contorno melódico global del bajo.

        Crea un arco independiente de la melodía:
        - Inicio: estable (grados bajos)
        - Desarrollo: ascenso hacia clímax
        - Clímax: punto más alto (hacia la mitad)
        - Resolución: descenso hacia cadencia

        Returns:
            Lista de direcciones objetivo: 1=subir, -1=bajar, 0=estable
        """
        contour = []
        climax_point = num_measures // 2

        for i in range(num_measures):
            if i < climax_point:
                # Ascenso hacia clímax
                contour.append(1)
            elif i == climax_point:
                # Clímax: puede saltar
                contour.append(1)
            elif i >= num_measures - 2:
                # Cadencia: descenso estable
                contour.append(-1)
            else:
                # Post-clímax: descenso gradual
                contour.append(-1)

        return contour

    def _select_contrapunto_rhythm(self) -> List[Tuple[int, int]]:
        """
        Selecciona un patrón rítmico variado para el contrapunto.

        Returns:
            Lista de duraciones (num, denom)
        """
        num_beats = self.meter_tuple[0]

        if num_beats == 4:
            return random.choice(self.CONTRAPUNTO_RHYTHMS_4_4)
        elif num_beats == 3:
            return random.choice(self.CONTRAPUNTO_RHYTHMS_3_4)
        else:
            # Fallback: negras
            return [(1, self.meter_tuple[1])] * num_beats

    def _generate_contrapunto_figure(
        self,
        target_degree: int,
        chord_tones: List[int],
        rhythm_pattern: List[Tuple[int, int]],
        prev_degree: Optional[int],
        contour_direction: int,
        melody_pitches: Optional[List[int]],
        measure_idx: int,
        is_climax: bool,
        is_cadence: bool,
    ) -> List[abjad.Note]:
        """
        Genera una figura melódica contrapuntística para un compás.

        Tipos de figuras:
        1. Escala (ascendente/descendente)
        2. Arpegio roto
        3. Bordadura doble
        4. Salto + paso
        5. Paso + salto

        Args:
            target_degree: Grado objetivo (raíz del acorde)
            chord_tones: Notas del acorde
            rhythm_pattern: Patrón rítmico a usar
            prev_degree: Grado anterior
            contour_direction: Dirección del contorno (1=subir, -1=bajar)
            melody_pitches: Pitches de la melodía
            measure_idx: Índice del compás
            is_climax: Si es el punto de clímax
            is_cadence: Si es cadencia

        Returns:
            Lista de notas Abjad
        """
        notes = []
        num_notes = len(rhythm_pattern)
        octave = self.config.octave

        # Elegir tipo de figura melódica
        if is_cadence:
            # Cadencia: movimiento hacia la tónica
            figure_type = "cadential"
        elif is_climax:
            # Clímax: salto grande + ornamento
            figure_type = "climax"
        else:
            # Elegir figura variada
            figure_type = random.choice([
                "scale", "scale",           # Escala (más común)
                "broken_arpeggio",          # Arpegio roto
                "neighbor",                 # Bordadura
                "leap_step",                # Salto + paso
                "step_leap",                # Paso + salto
            ])

        # Generar grados según tipo de figura
        degrees = self._create_melodic_figure(
            figure_type=figure_type,
            target_degree=target_degree,
            chord_tones=chord_tones,
            num_notes=num_notes,
            direction=contour_direction,
            prev_degree=prev_degree,
        )

        # Crear notas con el patrón rítmico
        for i, (degree, duration) in enumerate(zip(degrees, rhythm_pattern)):
            # Ajustar octava
            deg_octave = self._adjust_octave_for_range(degree, octave)

            # Primera nota siempre del acorde
            if i == 0 and degree not in chord_tones:
                degree = self._nearest_chord_tone(degree, chord_tones)

            # VERIFICAR Y CORREGIR CONSONANCIA con la melodía
            # Tiempos fuertes (i=0) requieren consonancia estricta
            is_strong_beat = (i == 0)
            degree = self._verify_and_fix_consonance(
                bass_degree=degree,
                chord_tones=chord_tones,
                melody_pitches=melody_pitches,
                measure_idx=measure_idx,
                note_idx=i,
                is_strong_beat=is_strong_beat,
                octave=deg_octave,
            )

            pitch_str = self._degree_to_pitch(degree, deg_octave)
            note = self._pitch_to_abjad(pitch_str, duration)
            notes.append(note)

        return notes

    def _create_melodic_figure(
        self,
        figure_type: str,
        target_degree: int,
        chord_tones: List[int],
        num_notes: int,
        direction: int,
        prev_degree: Optional[int],
    ) -> List[int]:
        """
        Crea los grados para una figura melódica específica.

        Args:
            figure_type: Tipo de figura
            target_degree: Grado objetivo
            chord_tones: Notas del acorde
            num_notes: Número de notas a generar
            direction: Dirección (1=subir, -1=bajar)
            prev_degree: Grado anterior

        Returns:
            Lista de grados
        """
        degrees = [target_degree]  # Primera nota siempre el objetivo

        if num_notes == 1:
            return degrees

        current = target_degree

        if figure_type == "scale":
            # Escala: movimiento por grados conjuntos
            for _ in range(num_notes - 1):
                if direction > 0:
                    current = (current % 7) + 1
                else:
                    current = ((current - 2) % 7) + 1
                degrees.append(current)

        elif figure_type == "broken_arpeggio":
            # Arpegio roto: notas del acorde en orden irregular
            arp_pattern = [0, 2, 1, 2, 0, 1]  # Índices en chord_tones
            for i in range(num_notes - 1):
                idx = arp_pattern[i % len(arp_pattern)]
                if idx < len(chord_tones):
                    degrees.append(chord_tones[idx])
                else:
                    degrees.append(chord_tones[0])

        elif figure_type == "neighbor":
            # Bordadura: nota + vecina + nota
            neighbor = current + direction
            if neighbor < 1:
                neighbor = 7
            elif neighbor > 7:
                neighbor = 1
            pattern = [current, neighbor, current, neighbor, current]
            for i in range(num_notes - 1):
                degrees.append(pattern[(i + 1) % len(pattern)])

        elif figure_type == "leap_step":
            # Salto grande + pasos para regresar
            leap_target = chord_tones[2] if len(chord_tones) > 2 else chord_tones[0]
            degrees.append(leap_target)
            current = leap_target
            # Pasos de regreso
            for _ in range(num_notes - 2):
                if current > target_degree:
                    current = ((current - 2) % 7) + 1
                else:
                    current = (current % 7) + 1
                degrees.append(current)

        elif figure_type == "step_leap":
            # Pasos preparatorios + salto
            prep_steps = min(2, num_notes - 2)
            for _ in range(prep_steps):
                current = current + direction
                if current < 1:
                    current = 7
                elif current > 7:
                    current = 1
                degrees.append(current)
            # Salto final
            leap_target = chord_tones[2] if len(chord_tones) > 2 else chord_tones[1]
            for _ in range(num_notes - 1 - prep_steps):
                degrees.append(leap_target)

        elif figure_type == "climax":
            # Clímax: salto a la quinta + ornamento
            fifth = chord_tones[2] if len(chord_tones) > 2 else chord_tones[0]
            degrees.append(fifth)
            # Ornamento alrededor de la quinta
            for i in range(num_notes - 2):
                if i % 2 == 0:
                    degrees.append(fifth + 1 if fifth < 7 else 1)
                else:
                    degrees.append(fifth)

        elif figure_type == "cadential":
            # Figura cadencial: V - I o sensible - tónica
            if num_notes >= 3:
                degrees.append(5)  # Dominante
                degrees.append(7)  # Sensible
            for _ in range(num_notes - len(degrees)):
                degrees.append(1)  # Tónica

        else:
            # Fallback: repetir nota
            for _ in range(num_notes - 1):
                degrees.append(target_degree)

        return degrees[:num_notes]

    def _get_melody_direction(
        self,
        melody_pitches: Optional[List[int]],
        measure_idx: int,
    ) -> int:
        """
        Determina la dirección general de la melodía en un compás.

        Returns:
            1 si asciende, -1 si desciende, 0 si estática/desconocida
        """
        if not melody_pitches or measure_idx >= len(melody_pitches) - 1:
            return 0

        current = melody_pitches[measure_idx]
        next_val = melody_pitches[measure_idx + 1] if measure_idx + 1 < len(melody_pitches) else current

        if next_val > current:
            return 1
        elif next_val < current:
            return -1
        return 0

    def _is_strong_beat(self, beat_idx: int, num_beats: int) -> bool:
        """
        Determina si un pulso es fuerte o débil.

        Args:
            beat_idx: Índice del pulso (0-based)
            num_beats: Total de pulsos

        Returns:
            True si es tiempo fuerte
        """
        if beat_idx == 0:
            return True  # Siempre fuerte

        if num_beats == 4:
            return beat_idx == 2  # 1 y 3 son fuertes (0 y 2 en 0-based)
        elif num_beats == 3:
            return False  # Solo el primero es fuerte en 3/4
        elif num_beats == 2:
            return False  # Solo el primero es fuerte en 2/4
        elif num_beats >= 6:
            return beat_idx % 3 == 0  # Compases compuestos

        return False

    def _select_stepwise_chord_tone(
        self,
        current_degree: int,
        chord_tones: List[int],
        direction: int,
    ) -> int:
        """
        Selecciona una nota del acorde preferiendo movimiento por grado conjunto.

        Args:
            current_degree: Grado actual
            chord_tones: Notas del acorde
            direction: Dirección preferida (1=arriba, -1=abajo)

        Returns:
            Grado seleccionado (garantizado del acorde)
        """
        # Calcular distancias a cada nota del acorde
        candidates = []
        for ct in chord_tones:
            # Distancia considerando wraparound
            dist = ct - current_degree
            if dist > 3:
                dist -= 7
            elif dist < -3:
                dist += 7

            # Preferir notas en la dirección correcta
            in_direction = (dist > 0 and direction > 0) or (dist < 0 and direction < 0)

            candidates.append({
                'degree': ct,
                'distance': abs(dist),
                'in_direction': in_direction,
            })

        # Ordenar: primero por dirección correcta, luego por cercanía
        candidates.sort(key=lambda x: (not x['in_direction'], x['distance']))

        # Probabilidad de elegir la más cercana vs variedad
        if random.random() < self.config.stepwise_preference:
            return candidates[0]['degree']
        else:
            # Elegir aleatoriamente entre las opciones válidas
            return random.choice(chord_tones)

    def _get_passing_tone(self, current_degree: int, direction: int) -> int:
        """
        Obtiene una nota de paso por grado conjunto.

        Args:
            current_degree: Grado actual
            direction: Dirección del movimiento

        Returns:
            Grado de la nota de paso
        """
        if direction > 0:
            # Ascendente
            next_deg = (current_degree % 7) + 1
        elif direction < 0:
            # Descendente
            next_deg = ((current_degree - 2) % 7) + 1
        else:
            # Sin dirección clara: elegir aleatoriamente
            if random.random() < 0.5:
                next_deg = (current_degree % 7) + 1
            else:
                next_deg = ((current_degree - 2) % 7) + 1

        return next_deg

    def _ensure_consonance_with_melody(
        self,
        bass_degree: int,
        chord_tones: List[int],
        melody_pitches: List[int],
        measure_idx: int,
    ) -> int:
        """
        Verifica y ajusta la consonancia entre bajo y melodía.

        Intervalos consonantes: 3ra, 5ta, 6ta, 8va (y sus compuestos)
        Intervalos disonantes: 2da, 7ma (evitar en tiempos fuertes)

        Args:
            bass_degree: Grado propuesto para el bajo
            chord_tones: Notas del acorde
            melody_pitches: Lista de pitches MIDI de la melodía
            measure_idx: Índice del compás

        Returns:
            Grado ajustado para consonancia
        """
        # Si no hay información de melodía, no ajustar
        if not melody_pitches or measure_idx >= len(melody_pitches):
            return bass_degree

        # Obtener pitch de melodía aproximado para este compás
        melody_midi = melody_pitches[measure_idx] if measure_idx < len(melody_pitches) else 60

        # Convertir bajo a MIDI aproximado
        pitch_str = self._degree_to_pitch(bass_degree, self.config.octave)
        from music21 import pitch as m21pitch
        bass_midi = m21pitch.Pitch(pitch_str).midi

        # Calcular intervalo
        interval_class = (melody_midi - bass_midi) % 12

        # Intervalos disonantes: 1 (2da menor), 2 (2da mayor), 10 (7ma menor), 11 (7ma mayor)
        dissonant = [1, 2, 10, 11]

        if interval_class in dissonant:
            # Buscar nota del acorde que sea consonante
            for ct in chord_tones:
                ct_pitch_str = self._degree_to_pitch(ct, self.config.octave)
                ct_midi = m21pitch.Pitch(ct_pitch_str).midi
                new_interval = (melody_midi - ct_midi) % 12

                if new_interval not in dissonant:
                    return ct

        return bass_degree

    def _verify_and_fix_consonance(
        self,
        bass_degree: int,
        chord_tones: List[int],
        melody_pitches: Optional[List[int]],
        measure_idx: int,
        note_idx: int,
        is_strong_beat: bool,
        octave: int,
    ) -> int:
        """
        Verifica y CORRIGE la consonancia entre bajo y melodía.

        Este método es ACTIVO: no solo detecta problemas, los soluciona.

        Reglas:
        - Tiempos fuertes: SOLO consonancias perfectas (3ra, 5ta, 6ta, 8va)
        - Tiempos débiles: toleran disonancias de paso (2da, 7ma)
        - Unísono y octava: evitar en tiempos débiles (demasiado "vacío")

        Args:
            bass_degree: Grado propuesto para el bajo
            chord_tones: Notas del acorde
            melody_pitches: Pitches MIDI de la melodía
            measure_idx: Índice del compás
            note_idx: Índice de la nota dentro del compás
            is_strong_beat: Si es tiempo fuerte
            octave: Octava del bajo

        Returns:
            Grado corregido (o el original si ya era consonante)
        """
        # Si no hay melodía, no podemos verificar
        if not melody_pitches:
            return bass_degree

        # Calcular número total de compases (estimado desde el contexto del generador)
        num_measures = max(1, getattr(self, '_current_num_measures', 8))

        # Estimar qué nota de la melodía corresponde a esta posición
        # Usar distribución uniforme de notas por compás
        total_melody_notes = len(melody_pitches)
        notes_per_measure = max(1, total_melody_notes // num_measures)

        # Índice aproximado en la melodía
        melody_note_idx = measure_idx * notes_per_measure + min(note_idx, notes_per_measure - 1)

        # Asegurar que está dentro de rango
        melody_note_idx = min(melody_note_idx, total_melody_notes - 1)
        melody_note_idx = max(0, melody_note_idx)

        melody_midi = melody_pitches[melody_note_idx]

        # Convertir bajo a MIDI
        from music21 import pitch as m21pitch
        pitch_str = self._degree_to_pitch(bass_degree, octave)
        try:
            bass_midi = m21pitch.Pitch(pitch_str).midi
        except Exception:
            return bass_degree  # Si falla conversión, mantener original

        # Calcular intervalo (clase de intervalo: 0-11)
        interval_class = abs(melody_midi - bass_midi) % 12

        # Clasificar intervalos
        # Consonancias perfectas: unísono(0), 5ta(7)
        # Consonancias imperfectas: 3ra menor(3), 3ra mayor(4), 6ta menor(8), 6ta mayor(9)
        # Disonancias: 2da menor(1), 2da mayor(2), 4ta(5), tritono(6), 7ma menor(10), 7ma mayor(11)

        consonant_perfect = {0, 7}  # unísono/octava, 5ta justa
        consonant_imperfect = {3, 4, 8, 9}  # 3ras y 6tas
        all_consonant = consonant_perfect | consonant_imperfect
        strong_dissonant = {1, 2, 10, 11}  # 2das y 7mas - SIEMPRE evitar

        # REGLA 1: Tiempos fuertes DEBEN ser consonantes
        if is_strong_beat:
            if interval_class not in all_consonant:
                # Buscar la MEJOR nota del acorde que sea consonante
                best_degree = None
                best_score = -1

                for ct in chord_tones:
                    ct_pitch_str = self._degree_to_pitch(ct, octave)
                    try:
                        ct_midi = m21pitch.Pitch(ct_pitch_str).midi
                        ct_interval = abs(melody_midi - ct_midi) % 12

                        # Puntuar: consonancias imperfectas > perfectas > otras
                        if ct_interval in consonant_imperfect:
                            score = 3  # Mejor: 3ras y 6tas (sonido rico)
                        elif ct_interval in consonant_perfect:
                            score = 2  # Bueno: 5tas y octavas
                        elif ct_interval not in strong_dissonant:
                            score = 1  # Aceptable: 4ta, tritono
                        else:
                            score = 0  # Evitar: 2das y 7mas

                        if score > best_score:
                            best_score = score
                            best_degree = ct
                    except Exception:
                        continue

                if best_degree is not None:
                    return best_degree

        # REGLA 2: Tiempos débiles - evitar disonancias fuertes (2das y 7mas)
        else:
            if interval_class in strong_dissonant:
                # Mover por grado conjunto para crear nota de paso válida
                # Dirección: alejarse de la disonancia
                if interval_class in {1, 2}:  # 2da - muy cerca
                    # Bajar el bajo para crear distancia
                    new_degree = ((bass_degree - 2) % 7) + 1
                else:  # 7ma - casi octava
                    # Subir el bajo para llegar a octava/unísono
                    new_degree = (bass_degree % 7) + 1

                # Verificar que el nuevo grado es mejor
                new_pitch_str = self._degree_to_pitch(new_degree, octave)
                try:
                    new_midi = m21pitch.Pitch(new_pitch_str).midi
                    new_interval = abs(melody_midi - new_midi) % 12
                    if new_interval not in strong_dissonant:
                        return new_degree
                except Exception:
                    pass

        return bass_degree

    def _nearest_chord_tone(self, degree: int, chord_tones: List[int]) -> int:
        """
        Encuentra la nota del acorde más cercana a un grado dado.

        Args:
            degree: Grado objetivo
            chord_tones: Notas del acorde

        Returns:
            Nota del acorde más cercana
        """
        min_dist = float('inf')
        nearest = chord_tones[0]

        for ct in chord_tones:
            # Distancia considerando envolvimiento de octava
            dist = min(abs(ct - degree), 7 - abs(ct - degree))
            if dist < min_dist:
                min_dist = dist
                nearest = ct

        return nearest

    def get_voice_leading_errors(self) -> List[VoiceLeadingError]:
        """Retorna la lista de errores de conducción de voces detectados."""
        return self._voice_leading_errors

    def verify_voice_leading(
        self,
        bass_staff: abjad.Staff,
        melody_staff: abjad.Staff,
        auto_fix: bool = True,
    ) -> List[VoiceLeadingError]:
        """
        Verifica y CORRIGE la conducción de voces entre bajo y melodía.

        Este método es ACTIVO: detecta quintas/octavas paralelas y las CORRIGE
        modificando el bajo para evitar el error.

        Args:
            bass_staff: Staff del bajo (SE MODIFICA IN-PLACE si auto_fix=True)
            melody_staff: Staff de la melodía
            auto_fix: Si True, corrige automáticamente los errores

        Returns:
            Lista de errores detectados (antes de corrección si auto_fix=True)
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
        min_len = min(len(bass_notes), len(melody_notes))

        for i in range(1, min_len):
            bass_curr = self._note_to_midi(bass_notes[i])
            bass_prev = self._note_to_midi(bass_notes[i-1])
            melody_curr = self._note_to_midi(melody_notes[i])
            melody_prev = self._note_to_midi(melody_notes[i-1])

            error_found = None

            # Verificar quintas paralelas
            if VoiceLeadingChecker.check_parallel_fifths(
                melody_curr, bass_curr, melody_prev, bass_prev
            ):
                error_found = VoiceLeadingError(
                    error_type="parallel_fifths",
                    measure_index=i,
                    description=f"Quintas paralelas en posición {i}"
                )
                errors.append(error_found)

            # Verificar octavas paralelas
            elif VoiceLeadingChecker.check_parallel_octaves(
                melody_curr, bass_curr, melody_prev, bass_prev
            ):
                error_found = VoiceLeadingError(
                    error_type="parallel_octaves",
                    measure_index=i,
                    description=f"Octavas paralelas en posición {i}"
                )
                errors.append(error_found)

            # CORREGIR si se encontró error y auto_fix está activo
            if error_found and auto_fix:
                self._fix_parallel_motion(
                    bass_notes[i],
                    bass_curr,
                    melody_curr,
                    error_found.error_type
                )

            # Verificar quintas directas (advertencia, no corregir)
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

    def _fix_parallel_motion(
        self,
        bass_note: abjad.Note,
        bass_midi: int,
        melody_midi: int,
        error_type: str,
    ) -> None:
        """
        Corrige una nota del bajo que causa movimiento paralelo prohibido.

        Estrategia de corrección:
        - Quintas paralelas: mover bajo una 3ra arriba o abajo
        - Octavas paralelas: mover bajo una 3ra arriba o abajo

        Args:
            bass_note: Nota del bajo a modificar (IN-PLACE)
            bass_midi: Valor MIDI actual del bajo
            melody_midi: Valor MIDI de la melodía
            error_type: "parallel_fifths" o "parallel_octaves"
        """
        # Calcular nueva nota: mover una 3ra menor (3 semitonos)
        # Preferir movimiento hacia consonancia imperfecta (3ra o 6ta)
        current_interval = abs(melody_midi - bass_midi) % 12

        # Si es 5ta (7) o 8va (0), ir a 3ra (3 o 4) o 6ta (8 o 9)
        if current_interval == 7:  # Quinta justa
            # Bajar 4 semitonos para ir a 3ra mayor
            new_bass_midi = bass_midi - 4
        elif current_interval == 0:  # Octava/unísono
            # Bajar 3 semitonos para ir a 3ra menor debajo
            new_bass_midi = bass_midi - 3
        else:
            # Mover 2 semitonos
            new_bass_midi = bass_midi - 2

        # Calcular nuevo pitch
        new_pitch_num = new_bass_midi - 60  # Convertir de MIDI a número Abjad

        # Crear nuevo pitch y asignar a la nota
        try:
            new_pitch = abjad.NamedPitch(new_pitch_num)
            bass_note.written_pitch = new_pitch
        except Exception:
            # Si falla, intentar ajuste más conservador
            try:
                conservative_midi = bass_midi - 1
                conservative_pitch = abjad.NamedPitch(conservative_midi - 60)
                bass_note.written_pitch = conservative_pitch
            except Exception:
                pass  # No se pudo corregir, mantener original

    def fix_dissonances_post_generation(
        self,
        bass_staff: abjad.Staff,
        melody_staff: abjad.Staff,
    ) -> int:
        """
        Corrección post-generación de disonancias basada en tiempo real.

        Este método analiza qué notas suenan SIMULTÁNEAMENTE y corrige
        las disonancias fuertes (2das y 7mas) en el bajo.

        Args:
            bass_staff: Staff del bajo (SE MODIFICA IN-PLACE)
            melody_staff: Staff de la melodía

        Returns:
            Número de correcciones realizadas
        """
        corrections = 0

        # Construir mapa temporal: offset -> nota
        def build_time_map(staff):
            time_map = {}
            current_offset = 0
            for leaf in abjad.iterate.leaves(staff):
                if isinstance(leaf, abjad.Note):
                    time_map[current_offset] = leaf
                duration = abjad.get.duration(leaf)
                # Convertir Duration a float
                current_offset += float(duration)
            return time_map

        melody_map = build_time_map(melody_staff)
        bass_notes = [(float(abjad.get.duration(n, preprolated=True)), n)
                      for n in abjad.iterate.leaves(bass_staff)
                      if isinstance(n, abjad.Note)]

        # Para cada nota del bajo, encontrar qué nota de melodía suena al mismo tiempo
        current_offset = 0
        for dur, bass_note in bass_notes:
            # Buscar la nota de melodía más cercana a este offset
            melody_note = None
            best_match = float('inf')

            for mel_offset, mel_note in melody_map.items():
                if abs(mel_offset - current_offset) < best_match:
                    best_match = abs(mel_offset - current_offset)
                    melody_note = mel_note

            if melody_note is not None:
                bass_midi = self._note_to_midi(bass_note)
                melody_midi = self._note_to_midi(melody_note)

                interval = abs(melody_midi - bass_midi) % 12

                # Disonancias fuertes: 2das (1, 2) y 7mas (10, 11)
                if interval in {1, 2, 10, 11}:
                    # Corregir moviendo el bajo
                    self._fix_dissonance(bass_note, bass_midi, melody_midi, interval)
                    corrections += 1

            current_offset += dur

        return corrections

    def _fix_dissonance(
        self,
        bass_note: abjad.Note,
        bass_midi: int,
        melody_midi: int,
        interval: int,
    ) -> None:
        """
        Corrige una disonancia fuerte moviendo el bajo a una consonancia.

        Busca la consonancia más cercana y mueve el bajo allí.
        Consonancias objetivo: 3ra menor(3), 3ra mayor(4), 5ta(7), 6ta menor(8), 6ta mayor(9)

        Args:
            bass_note: Nota del bajo a modificar
            bass_midi: MIDI actual del bajo
            melody_midi: MIDI de la melodía
            interval: Clase de intervalo (1, 2, 10, 11)
        """
        # Consonancias objetivo ordenadas por preferencia musical
        # Preferimos 3ras y 6tas (consonancias imperfectas) sobre 5tas/8vas
        consonances = [3, 4, 8, 9, 7, 0]  # 3ra-, 3ra+, 6ta-, 6ta+, 5ta, 8va

        # Encontrar la consonancia más cercana
        best_new_midi = bass_midi
        min_movement = float('inf')

        for target_interval in consonances:
            # Calcular nuevo MIDI del bajo para lograr este intervalo
            # melody_midi - new_bass_midi = target_interval (mod 12)
            # new_bass_midi = melody_midi - target_interval

            # Probar en ambas octavas
            for octave_adj in [0, -12, 12]:
                candidate = melody_midi - target_interval + octave_adj

                # Verificar que está en rango razonable del bajo (C2-C4 aprox)
                if 36 <= candidate <= 72:  # Rango del bajo
                    movement = abs(candidate - bass_midi)
                    if movement < min_movement:
                        min_movement = movement
                        best_new_midi = candidate

        # Aplicar corrección
        if best_new_midi != bass_midi:
            new_pitch_num = best_new_midi - 60
            try:
                new_pitch = abjad.NamedPitch(new_pitch_num)
                bass_note.written_pitch = new_pitch
            except Exception:
                pass  # No se pudo corregir

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

    # =========================================================================
    # CONTROL DE RANGO Y EXPRESIÓN MUSICAL
    # =========================================================================

    def _validate_pitch_in_range(self, midi_pitch: int) -> int:
        """
        Valida y ajusta un pitch MIDI para que esté dentro del rango del bajo.

        Args:
            midi_pitch: Valor MIDI del pitch

        Returns:
            Pitch MIDI ajustado al rango válido
        """
        # Si está fuera del rango absoluto, ajustar por octavas
        while midi_pitch < self.config.min_pitch:
            midi_pitch += 12
        while midi_pitch > self.config.max_pitch:
            midi_pitch -= 12

        return midi_pitch

    def _adjust_octave_for_range(self, degree: int, base_octave: int) -> int:
        """
        Ajusta la octava para mantener el pitch dentro del rango preferido.

        Args:
            degree: Grado de la escala (1-7)
            base_octave: Octava base

        Returns:
            Octava ajustada
        """
        # Obtener pitch y verificar rango
        pitch_str = self._degree_to_pitch(degree, base_octave)
        from music21 import pitch as m21pitch
        p = m21pitch.Pitch(pitch_str)
        midi = int(p.midi)

        # Preferir el rango central
        if midi < self.config.preferred_min:
            return base_octave + 1
        elif midi > self.config.preferred_max:
            return base_octave - 1

        return base_octave

    def apply_expression(self, staff: abjad.Staff, num_measures: int) -> abjad.Staff:
        """
        Aplica expresiones musicales al bajo (dinámicas, articulaciones, slurs).

        Args:
            staff: Staff del bajo
            num_measures: Número de compases

        Returns:
            Staff con expresiones aplicadas
        """
        if self.config.use_dynamics:
            self._apply_dynamics(staff, num_measures)

        if self.config.use_articulations:
            self._apply_articulations(staff, num_measures)

        if self.config.use_slurs:
            self._apply_slurs(staff, num_measures)

        return staff

    def _apply_dynamics(self, staff: abjad.Staff, num_measures: int) -> None:
        """
        Aplica dinámicas al bajo.

        El bajo generalmente es más suave que la melodía y sigue
        una curva dinámica complementaria.
        """
        notes = [n for n in abjad.iterate.leaves(staff) if isinstance(n, abjad.Note)]
        if not notes:
            return

        # Niveles dinámicos para el bajo (más suaves que melodía)
        dynamics_map = {
            -2: "pp",
            -1: "p",
            0: "mp",
            1: "mf",
            2: "f",
        }

        # Dinámica base para bajo (offset aplicado)
        base_offset = self.config.dynamic_offset
        base_dynamic = dynamics_map.get(base_offset, "mp")

        # Aplicar dinámica inicial
        if notes:
            abjad.attach(abjad.Dynamic(base_dynamic), notes[0])

        # Aplicar crescendo/diminuendo en puntos estructurales
        notes_per_measure = max(1, len(notes) // num_measures)

        # Crescendo hacia la mitad (clímax)
        mid_point = len(notes) // 2
        if mid_point > 2:
            # Crescendo al inicio de la segunda mitad
            quarter_point = len(notes) // 4
            if quarter_point < len(notes):
                abjad.attach(abjad.StartHairpin("<"), notes[quarter_point])

            # Dinámica más fuerte en el clímax
            climax_dynamic = dynamics_map.get(base_offset + 1, "mf")
            if mid_point < len(notes):
                abjad.attach(abjad.Dynamic(climax_dynamic), notes[mid_point])

        # Diminuendo hacia el final
        three_quarter = (3 * len(notes)) // 4
        if three_quarter < len(notes) - 1:
            abjad.attach(abjad.StartHairpin(">"), notes[three_quarter])

        # Dinámica final (suave para cadencia)
        if len(notes) > 1:
            final_dynamic = dynamics_map.get(base_offset - 1, "p")
            abjad.attach(abjad.Dynamic(final_dynamic), notes[-1])

    def _apply_articulations(self, staff: abjad.Staff, num_measures: int) -> None:
        """
        Aplica articulaciones al bajo según el estilo.

        Estilos:
        - "sustained": más tenuto, menos staccato (por defecto)
        - "detached": más staccato, marcato
        - "mixed": combinación balanceada
        """
        notes = [n for n in abjad.iterate.leaves(staff) if isinstance(n, abjad.Note)]
        if len(notes) < 2:
            return

        style = self.config.articulation_style

        for i, note in enumerate(notes):
            # Primera nota: tenuto para establecer el bajo
            if i == 0:
                abjad.attach(abjad.Articulation("tenuto"), note)
                continue

            # Última nota: tenuto o fermata si es cadencia final
            if i == len(notes) - 1:
                abjad.attach(abjad.Articulation("tenuto"), note)
                continue

            # Calcular intervalo con nota anterior
            prev_midi = self._note_to_midi(notes[i - 1])
            curr_midi = self._note_to_midi(note)
            interval = abs(curr_midi - prev_midi)

            # Aplicar articulación según estilo y contexto
            if style == "sustained":
                # Estilo sostenido: tenuto en tiempos fuertes, nada en otros
                if i % 4 == 0:  # Tiempo fuerte (aproximado)
                    abjad.attach(abjad.Articulation("tenuto"), note)
                elif interval >= 5:  # Salto grande: acento suave
                    abjad.attach(abjad.Articulation("accent"), note)

            elif style == "detached":
                # Estilo separado: staccato frecuente
                if interval == 0:  # Nota repetida
                    abjad.attach(abjad.Articulation("staccato"), note)
                elif interval >= 7:  # Salto de quinta o más
                    abjad.attach(abjad.Articulation("marcato"), note)
                elif i % 2 == 0:
                    abjad.attach(abjad.Articulation("staccato"), note)

            else:  # mixed
                # Estilo mixto: balance de articulaciones
                if interval == 0:
                    abjad.attach(abjad.Articulation("staccato"), note)
                elif interval >= 7:
                    abjad.attach(abjad.Articulation("accent"), note)
                elif i % 4 == 0:
                    abjad.attach(abjad.Articulation("tenuto"), note)

    def _apply_slurs(self, staff: abjad.Staff, num_measures: int) -> None:
        """
        Aplica ligaduras de fraseo (slurs) al bajo.

        Las ligaduras agrupan notas por frase musical,
        típicamente 2-4 compases.
        """
        notes = [n for n in abjad.iterate.leaves(staff) if isinstance(n, abjad.Note)]
        if len(notes) < 4:
            return

        notes_per_measure = max(1, len(notes) // num_measures)

        # Determinar longitud de frase según estilo de bajo
        if self.config.style == BassStyle.SIMPLE:
            # Bajo simple: slurs cada 2 compases
            phrase_length = notes_per_measure * 2
        elif self.config.style == BassStyle.ALBERTI:
            # Alberti: slurs cada compás (arpegio completo)
            phrase_length = notes_per_measure
        else:  # WALKING
            # Walking: slurs cada 2 compases
            phrase_length = notes_per_measure * 2

        # Aplicar slurs por frases
        i = 0
        while i < len(notes) - 1:
            # Calcular fin de la frase
            end = min(i + phrase_length - 1, len(notes) - 1)

            # Solo aplicar slur si hay al menos 2 notas
            if end > i:
                try:
                    abjad.attach(abjad.StartSlur(), notes[i])
                    abjad.attach(abjad.StopSlur(), notes[end])
                except Exception:
                    # Si hay conflicto de slurs, ignorar
                    pass

            i = end + 1

    def get_range_info(self) -> dict:
        """
        Retorna información sobre el rango configurado del bajo.

        Returns:
            Dict con información de rango en formato legible
        """
        from music21 import pitch as m21pitch

        def midi_to_name(midi: int) -> str:
            p = m21pitch.Pitch(midi=midi)
            return f"{p.nameWithOctave}"

        return {
            "min_pitch": midi_to_name(self.config.min_pitch),
            "max_pitch": midi_to_name(self.config.max_pitch),
            "preferred_min": midi_to_name(self.config.preferred_min),
            "preferred_max": midi_to_name(self.config.preferred_max),
            "range_semitones": self.config.max_pitch - self.config.min_pitch,
        }
