"""
Generador de Melodías según Teoría Musical Clásica
Implementa el "Protocolo Symmetry & Logic" con soporte para:
- Jerarquía estructural: Motivo → Semifrase → Antecedente/Consecuente → Período
- Métricas regulares y amalgama (5/8, 7/8, 11/8, etc.)
- Sistema de notas estructurales vs. notas de paso
- Cadencias auténticas y semicadencias
- Sistema de infracción y compensación controlada
"""

import random
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional
from fractions import Fraction
import abjad
from music21 import key, pitch, interval, scale


def create_modal_scale(tonic_name: str, mode_type: str, mode_number: int = 1):
    """
    Crea una escala modal derivada de menor armónica o menor melódica.

    Args:
        tonic_name: Nombre de la tónica (ej: 'C', 'D', 'F#')
        mode_type: Tipo de modo base ('harmonic_minor' o 'melodic_minor')
        mode_number: Número del modo (1-7)

    Returns:
        ConcreteScale con los pitches del modo derivado
    """
    # Crear la escala base
    if mode_type == "harmonic_minor":
        base_scale = scale.HarmonicMinorScale(tonic_name)
    elif mode_type == "melodic_minor":
        base_scale = scale.MelodicMinorScale(tonic_name)
    else:
        raise ValueError(f"Tipo de modo no válido: {mode_type}")

    # Obtener los pitches de la escala base
    base_pitches = base_scale.pitches[:7]  # Solo los 7 primeros (sin octava)

    # Rotar para obtener el modo deseado (modo 1 = sin rotación)
    rotation = mode_number - 1
    rotated_pitches = base_pitches[rotation:] + base_pitches[:rotation]

    # Normalizar a la tónica deseada (transponer)
    target_tonic = pitch.Pitch(tonic_name + "4")
    source_tonic = rotated_pitches[0]

    # Calcular intervalo de transposición
    transp_interval = interval.Interval(noteStart=source_tonic, noteEnd=target_tonic)

    # Aplicar transposición
    modal_pitches = [transp_interval.transposePitch(p) for p in rotated_pitches]

    # Agregar la octava superior
    modal_pitches.append(modal_pitches[0].transpose("P8"))

    return scale.ConcreteScale(pitches=modal_pitches)


class ImpulseType(Enum):
    """Tipo de impulso inicial del motivo"""

    TETIC = "tetic"  # Comienza en tiempo fuerte
    ANACROUSTIC = "anacroustic"  # Comienza antes del tiempo fuerte
    ACEPHALOUS = "acephalous"  # Comienza después del tiempo fuerte


class NoteFunction(Enum):
    """Función de una nota en la jerarquía tonal"""

    STRUCTURAL = "structural"  # Nota del acorde (I, III, V)
    PASSING = "passing"  # Nota de paso
    NEIGHBOR = "neighbor"  # Bordadura
    APPOGGIATURA = "appoggiatura"  # Apoyatura


class MotivicVariation(Enum):
    """Tipos de variación motívica según teoría musical clásica"""

    ORIGINAL = "original"  # Motivo original sin variación
    INVERSION = "inversion"  # Inversión interválica
    RETROGRADE = "retrograde"  # Retrogradación (backwards)
    RETROGRADE_INVERSION = "retrograde_inversion"  # Retrogradación + inversión
    AUGMENTATION = "augmentation"  # Aumentación rítmica (valores más largos)
    DIMINUTION = "diminution"  # Disminución rítmica (valores más cortos)
    TRANSPOSITION = "transposition"  # Transposición a otro grado
    SEQUENCE = "sequence"  # Secuencia (repetición transpuesta)


@dataclass
class RhythmicPattern:
    """Patrón rítmico para un motivo"""

    durations: List[Tuple[int, int]]  # Lista de (numerador, denominador)
    strong_beat_indices: List[int]  # Índices de pulsos fuertes


@dataclass
class Motif:
    """Representa un motivo melódico"""

    pitches: List[str]  # Lista de pitches (ej: ["c'4", "d'4", "e'4"])
    intervals: List[int]  # Intervalos en semitonos entre notas consecutivas
    rhythm: RhythmicPattern  # Patrón rítmico del motivo
    degrees: List[int]  # Grados de la escala


@dataclass
class MelodicContour:
    """Control del contorno melódico y clímax"""

    max_range: int = 12  # Rango máximo en semitonos
    climax_position: float = 0.75  # Posición del clímax (0.0-1.0)
    prefer_stepwise: float = 0.7  # Probabilidad de movimiento por grado conjunto
    climax_approach_range: int = 3  # Compases de aproximación al clímax
    climax_emphasis: float = (
        1.5  # Factor de énfasis del clímax (multiplicador de registro)
    )


@dataclass
class HarmonicFunction:
    """Función armónica implícita para un compás o grupo de compases"""

    degree: int  # Grado del acorde (1=I, 4=IV, 5=V, etc.)
    quality: str  # "major", "minor", "diminished", "augmented"
    tension: float  # Nivel de tensión (0.0=reposo, 1.0=máxima tensión)
    chord_tones: List[int]  # Grados de la escala que forman el acorde


@dataclass
class Phrase:
    """Frase musical: motivo + respuesta/variación (típicamente 2 compases)"""

    motif: Motif  # Motivo base
    variation: Motif  # Variación/respuesta del motivo
    harmonic_progression: List[HarmonicFunction]  # Progresión armónica de la frase
    measure_range: Tuple[int, int]  # (inicio, fin) en índices de compases


@dataclass
class Semiphrase:
    """Semifrase: agrupación de frases (típicamente 4 compases)"""

    phrases: List[Phrase]  # Lista de frases que componen la semifrase
    function: str  # "presentation", "development", "cadential"
    measure_range: Tuple[int, int]  # (inicio, fin) en índices de compases


@dataclass
class Period:
    """Período: antecedente + consecuente (típicamente 8 compases)"""

    antecedent: Semiphrase  # Semifrase antecedente (pregunta)
    consequent: Semiphrase  # Semifrase consecuente (respuesta)
    total_measures: int  # Número total de compases
    base_motif: Motif  # Motivo generador de todo el período


class MelodicArchitect:
    """
    Arquitecto melódico basado en teoría musical clásica.
    Implementa el algoritmo "Symmetry & Logic" en tres capas:
    I. Configuración de la Realidad Musical
    II. Generación del ADN (Motivo y Frase)
    III. Desarrollo y Cierre (Período y Cadencia)
    """

    def __init__(
        self,
        key_name: str = "C",
        mode: str = "major",
        meter_tuple: Tuple[int, int] = (4, 4),
        subdivisions: Optional[List[int]] = None,
        num_measures: int = 8,
        impulse_type: ImpulseType = ImpulseType.TETIC,
        infraction_rate: float = 0.1,
        rhythmic_complexity: int = 3,
        use_rests: bool = True,
        rest_probability: float = 0.15,
        use_motivic_variations: bool = True,
        variation_probability: float = 0.4,
        climax_position: float = 0.75,
        climax_intensity: float = 1.5,
        max_interval: int = 6,  # Máximo salto permitido (sexta)
        use_tenoris: bool = False,  # Usar quinta como nota sostenedora
        tenoris_probability: float = 0.2,  # Probabilidad de usar tenoris
        variation_freedom: int = 2,  # Libertad de variación (1=estricta, 2=moderada, 3=libre)
    ):
        """
        Inicializa el arquitecto melódico.

        Args:
            key_name: Nombre de la tonalidad (ej: "C", "D", "Eb")
            mode: Modo musical ("major", "minor", "dorian", "phrygian", "lydian", "mixolydian")
            meter_tuple: Compás (numerador, denominador)
            subdivisions: Para métricas amalgama, subdivisión de pulsos (ej: [2,3] para 5/8)
            num_measures: Número de compases del período
            impulse_type: Tipo de impulso inicial
            infraction_rate: Tasa de infracción (0.0-1.0, creatividad vs rigidez)
            rhythmic_complexity: Complejidad rítmica (1=simple, 5=complejo)
            use_rests: Si se deben usar silencios como respiraciones
            rest_probability: Probabilidad de usar silencio (0.0-1.0)
            use_motivic_variations: Si se deben aplicar variaciones motívicas
            variation_probability: Probabilidad de aplicar variación (0.0-1.0)
            climax_position: Posición del clímax melódico (0.0-1.0)
            climax_intensity: Intensidad del clímax (multiplicador de registro)
        """
        # Capa I: Configuración de la Realidad Musical
        self.key_name = key_name
        self.mode = mode
        self.k = (
            key.Key(key_name) if mode == "major" else key.Key(key_name, mode="minor")
        )

        # Configurar escala según modo
        # MODOS DE ESCALA MAYOR (diatónicos)
        if mode == "major":
            self.scale = scale.MajorScale(key_name)
        elif mode == "dorian":
            self.scale = scale.DorianScale(key_name)
        elif mode == "phrygian":
            self.scale = scale.PhrygianScale(key_name)
        elif mode == "lydian":
            self.scale = scale.LydianScale(key_name)
        elif mode == "mixolydian":
            self.scale = scale.MixolydianScale(key_name)
        elif mode == "minor":  # Aeolian (menor natural)
            self.scale = scale.MinorScale(key_name)
        elif mode == "locrian":
            self.scale = scale.LocrianScale(key_name)

        # ESCALAS MENORES
        elif mode == "harmonic_minor":
            self.scale = scale.HarmonicMinorScale(key_name)
        elif mode == "melodic_minor":
            self.scale = scale.MelodicMinorScale(key_name)

        # MODOS DE MENOR ARMÓNICA
        elif mode == "locrian_nat6":  # Modo 2
            self.scale = create_modal_scale(key_name, "harmonic_minor", 2)
        elif mode == "ionian_aug5":  # Modo 3
            self.scale = create_modal_scale(key_name, "harmonic_minor", 3)
        elif mode == "dorian_sharp4":  # Modo 4 (Ucraniano)
            self.scale = create_modal_scale(key_name, "harmonic_minor", 4)
        elif mode == "phrygian_dominant":  # Modo 5 (Frigio mayor)
            self.scale = create_modal_scale(key_name, "harmonic_minor", 5)
        elif mode == "lydian_sharp2":  # Modo 6
            self.scale = create_modal_scale(key_name, "harmonic_minor", 6)
        elif mode == "superlocrian_bb7":  # Modo 7 (Ultralocrio)
            self.scale = create_modal_scale(key_name, "harmonic_minor", 7)

        # MODOS DE MENOR MELÓDICA
        elif mode == "dorian_flat2":  # Modo 2 (Frigio #6)
            self.scale = create_modal_scale(key_name, "melodic_minor", 2)
        elif mode == "lydian_augmented":  # Modo 3 (Lidio #5)
            self.scale = create_modal_scale(key_name, "melodic_minor", 3)
        elif mode == "lydian_dominant":  # Modo 4 (Lidio b7 / Mixolidio #4)
            self.scale = create_modal_scale(key_name, "melodic_minor", 4)
        elif mode == "mixolydian_flat6":  # Modo 5 (Aeolian nat7)
            self.scale = create_modal_scale(key_name, "melodic_minor", 5)
        elif mode == "locrian_nat2":  # Modo 6 (Semilocrio)
            self.scale = create_modal_scale(key_name, "melodic_minor", 6)
        elif mode == "altered":  # Modo 7 (Superlocrio / Locrio b4)
            self.scale = create_modal_scale(key_name, "melodic_minor", 7)

        else:
            self.scale = scale.MajorScale(key_name)

        # Configuración métrica
        self.meter_tuple = meter_tuple
        self.subdivisions = subdivisions or [meter_tuple[0]]
        self.num_measures = num_measures
        self.impulse_type = impulse_type

        # Parámetros de control
        self.infraction_rate = infraction_rate
        self.rhythmic_complexity = rhythmic_complexity
        self.use_rests = use_rests
        self.rest_probability = rest_probability
        self.use_motivic_variations = use_motivic_variations
        self.variation_probability = variation_probability

        # Control del clímax melódico
        self.contour = MelodicContour(
            climax_position=climax_position, climax_emphasis=climax_intensity
        )

        # Estado interno
        self.current_octave = 4
        self.last_pitch = None
        self.last_interval_direction = None  # Para recuperación de saltos
        self.phrase_highest_pitch = None
        self.phrase_lowest_pitch = None
        self.infraction_pending_compensation = False
        self.last_was_rest = False
        self.must_recover_leap = False  # Flag para forzar recuperación de salto

        # Control del clímax
        self.climax_measure = int(num_measures * climax_position)
        self.climax_reached = False
        self.current_highest_pitch = None

        # Motivo original para variaciones
        self.original_motif: Optional[Motif] = None
        self.current_variation: MotivicVariation = MotivicVariation.ORIGINAL

        # NUEVO: Motivo rítmico base (para cohesión melódica)
        # Se genera una sola vez y se reutiliza con variaciones
        self.base_rhythmic_motif: Optional[RhythmicPattern] = None

        # Reglas melódicas teóricas
        self.max_interval = max_interval
        self.use_tenoris = use_tenoris
        self.tenoris_probability = tenoris_probability

        # Control de libertad de variación (1=estricta, 2=moderada, 3=libre)
        self.variation_freedom = variation_freedom

        # Ámbito melódico: octava de la tónica ± cuarta
        # Base: octava 4 (C4-C5)
        # Extensión: -P4 (abajo) y +P4 (arriba)
        tonic_pitch = self.k.tonic
        tonic_base = pitch.Pitch(f"{tonic_pitch.name}4")

        # Calcular rango: tónica - cuarta hasta tónica + octava + cuarta
        self.melodic_range_bottom = tonic_base.transpose("-P4")  # G4 - P4 = D4
        self.melodic_range_top = tonic_base.transpose("P8").transpose(
            "P4"
        )  # G4 + P8 + P4 = C6

        # Calcular pulsos fuertes de la métrica amalgama
        self.strong_beats = self._calculate_strong_beats()

    def _calculate_strong_beats(self) -> List[int]:
        """Calcula los pulsos fuertes según la subdivisión de la métrica amalgama."""
        strong = [0]  # El primer pulso siempre es fuerte
        accumulated = 0
        for subdivision in self.subdivisions[:-1]:
            accumulated += subdivision
            strong.append(accumulated)
        return strong

    def get_pitch_by_degree(self, degree: int, octave: Optional[int] = None) -> str:
        """
        Retorna una nota de la escala por su grado (1-7).

        Args:
            degree: Grado de la escala (1-7)
            octave: Octava opcional, usa current_octave si no se especifica
        """
        if octave is None:
            octave = self.current_octave

        p = self.scale.pitchFromDegree(degree)
        return f"{p.name.lower().replace('-', 'b')}{octave}"

    def is_chord_tone(self, degree: int) -> bool:
        """Determina si un grado es nota del acorde tónico (I, III, V)."""
        return degree in [1, 3, 5]

    def is_tendency_tone(self, degree: int) -> bool:
        """Determina si un grado es nota de tendencia (VII, IV)."""
        return degree in [7, 4]

    def get_harmonic_function(self, measure_index: int, beat_index: int) -> int:
        """
        Retorna el acorde implícito para un punto específico.
        Implementa progresión armónica básica: I - V - I con variaciones.

        Returns:
            1 para tónica (I), 5 para dominante (V), 4 para subdominante (IV)
        """
        total_measures = self.num_measures
        is_antecedent = measure_index < total_measures // 2
        is_final_measure = measure_index == total_measures - 1
        is_semifinal_measure = measure_index == (total_measures // 2) - 1

        # Antecedente termina en V (semicadencia)
        if is_semifinal_measure and beat_index >= len(self.strong_beats) - 1:
            return 5

        # Consecuente termina en I (cadencia auténtica)
        if is_final_measure and beat_index >= len(self.strong_beats) - 1:
            return 1

        # Progresión armónica por medida
        if measure_index % 4 == 0:
            return 1  # Tónica
        elif measure_index % 4 == 1:
            return 4 if random.random() < 0.4 else 1  # Subdominante o tónica
        elif measure_index % 4 == 2:
            return 5  # Dominante
        else:
            return 1  # Tónica

    def get_chord_tones_for_function(self, harmonic_function: int) -> List[int]:
        """Retorna los grados de la escala que forman el acorde."""
        if harmonic_function == 1:  # Tónica
            return [1, 3, 5]
        elif harmonic_function == 4:  # Subdominante
            return [4, 6, 1]
        elif harmonic_function == 5:  # Dominante
            return [5, 7, 2]
        return [1, 3, 5]

    def calculate_climax_influence(self, measure_index: int) -> float:
        """
        Calcula el factor de influencia del clímax en el registro actual.

        Returns:
            Factor multiplicador para el registro (1.0 = normal, >1.0 = más agudo)
        """
        distance_to_climax = abs(measure_index - self.climax_measure)
        approach_range = self.contour.climax_approach_range

        if measure_index == self.climax_measure:
            # En el clímax: máximo registro
            return self.contour.climax_emphasis
        elif distance_to_climax <= approach_range:
            # Cerca del clímax: aproximación gradual
            proximity = 1.0 - (distance_to_climax / approach_range)
            return 1.0 + (self.contour.climax_emphasis - 1.0) * proximity
        else:
            # Lejos del clímax: registro normal
            return 1.0

    def apply_motivic_variation(
        self, degrees: List[int], variation_type: MotivicVariation
    ) -> List[int]:
        """
        Aplica una variación motívica a una secuencia de grados.

        Args:
            degrees: Lista de grados originales
            variation_type: Tipo de variación a aplicar

        Returns:
            Lista de grados con la variación aplicada
        """
        if variation_type == MotivicVariation.ORIGINAL:
            return degrees

        elif variation_type == MotivicVariation.INVERSION:
            # Inversión: los intervalos se invierten (sube→baja, baja→sube)
            if len(degrees) < 2:
                return degrees
            result = [degrees[0]]
            for i in range(1, len(degrees)):
                interval_original = degrees[i] - degrees[i - 1]
                new_degree = result[-1] - interval_original
                # Mantener en rango 1-7
                while new_degree < 1:
                    new_degree += 7
                while new_degree > 7:
                    new_degree -= 7
                result.append(new_degree)
            return result

        elif variation_type == MotivicVariation.RETROGRADE:
            # Retrogradación: tocar al revés
            return list(reversed(degrees))

        elif variation_type == MotivicVariation.RETROGRADE_INVERSION:
            # Retrogradación + inversión
            reversed_degrees = list(reversed(degrees))
            return self.apply_motivic_variation(
                reversed_degrees, MotivicVariation.INVERSION
            )

        elif variation_type == MotivicVariation.TRANSPOSITION:
            # Transposición: mover todo a otro grado
            transpose_interval = random.choice(
                [2, 3, 4, 5]
            )  # Transponer 2da, 3ra, 4ta o 5ta
            result = []
            for deg in degrees:
                new_deg = deg + transpose_interval
                while new_deg > 7:
                    new_deg -= 7
                result.append(new_deg)
            return result

        elif variation_type == MotivicVariation.SEQUENCE:
            # Secuencia: repetir transpuesto (similar a transposición para este contexto)
            return self.apply_motivic_variation(degrees, MotivicVariation.TRANSPOSITION)

        return degrees

    def apply_rhythmic_variation(
        self, durations: List[Tuple[int, int]], variation_type: MotivicVariation
    ) -> List[Tuple[int, int]]:
        """
        Aplica variación rítmica (aumentación o disminución).

        Args:
            durations: Lista de duraciones originales
            variation_type: Tipo de variación

        Returns:
            Lista de duraciones variadas
        """
        if variation_type == MotivicVariation.AUGMENTATION:
            # Aumentación: valores más largos (multiplicar por 2)
            return [(num * 2, denom) for num, denom in durations]

        elif variation_type == MotivicVariation.DIMINUTION:
            # Disminución: valores más cortos (dividir por 2)
            result = []
            for num, denom in durations:
                if num >= 2:
                    result.append((num // 2, denom))
                else:
                    result.append((num, denom * 2))
            return result

        return durations

    def select_variation_type(self, measure_index: int) -> MotivicVariation:
        """
        Selecciona un tipo de variación motívica según el contexto.

        Args:
            measure_index: Índice del compás actual

        Returns:
            Tipo de variación a aplicar
        """
        if not self.use_motivic_variations:
            return MotivicVariation.ORIGINAL

        if random.random() > self.variation_probability:
            return MotivicVariation.ORIGINAL

        # Cerca del clímax, preferir variaciones más dramáticas
        distance_to_climax = abs(measure_index - self.climax_measure)

        if distance_to_climax <= 1:
            # Cerca del clímax: inversión o aumentación
            return random.choice(
                [
                    MotivicVariation.INVERSION,
                    MotivicVariation.AUGMENTATION,
                    MotivicVariation.SEQUENCE,
                ]
            )
        elif measure_index < self.climax_measure:
            # Antes del clímax: variaciones que construyen tensión
            return random.choice(
                [
                    MotivicVariation.TRANSPOSITION,
                    MotivicVariation.SEQUENCE,
                    MotivicVariation.ORIGINAL,
                ]
            )
        else:
            # Después del clímax: variaciones más suaves
            return random.choice(
                [
                    MotivicVariation.RETROGRADE,
                    MotivicVariation.DIMINUTION,
                    MotivicVariation.ORIGINAL,
                ]
            )

    def _get_rhythmic_pattern_with_variation(
        self, measure_index: int
    ) -> RhythmicPattern:
        """
        Obtiene el patrón rítmico para este compás, aplicando variaciones al motivo base.

        PRINCIPIO (tarea.md líneas 128-130):
        "Economía de materiales": Reutilizar el motivo rítmico inicial con variaciones
        sutiles en lugar de generar ritmos completamente nuevos.

        Args:
            measure_index: Índice del compás (0 = primer compás)

        Returns:
            RhythmicPattern basado en el motivo original con posibles variaciones
        """
        # Si no existe motivo base, generar uno nuevo (debería haberse creado en generate_period)
        if self.base_rhythmic_motif is None:
            return self.create_rhythmic_pattern(self.meter_tuple[0])

        # Primer compás: usar motivo original sin cambios
        if measure_index == 0:
            return self.base_rhythmic_motif

        # Segundo compás: repetir motivo exacto (establecer identidad)
        if measure_index == 1:
            return self.base_rhythmic_motif

        # Cadencias: usar motivo original (claridad estructural)
        midpoint = self.num_measures // 2
        is_antecedent_end = measure_index == midpoint - 1
        is_period_end = measure_index == self.num_measures - 1

        if is_antecedent_end or is_period_end:
            return self.base_rhythmic_motif

        # Otros compases: aplicar variaciones sutiles con probabilidad
        if random.random() < 0.3:  # 30% de variación
            return self._apply_rhythmic_variation(self.base_rhythmic_motif)
        else:
            # 70% del tiempo: mantener motivo original
            return self.base_rhythmic_motif

    def _apply_rhythmic_variation(self, motif: RhythmicPattern) -> RhythmicPattern:
        """
        Aplica una variación sutil al motivo rítmico manteniendo su identidad.

        Variaciones posibles:
        - Retrogradación: Tocar el motivo al revés
        - Mantener: Sin cambios (para estabilidad)

        Args:
            motif: Motivo rítmico original

        Returns:
            Motivo variado
        """
        variation_type = random.choice(["retrograde", "original", "original"])

        if variation_type == "retrograde":
            # Retrogradación: invertir el orden de las duraciones
            reversed_durations = list(reversed(motif.durations))
            return RhythmicPattern(
                durations=reversed_durations,
                strong_beat_indices=motif.strong_beat_indices,
            )
        else:
            # Mantener original
            return motif

    def create_rhythmic_pattern(self, num_beats: int) -> RhythmicPattern:
        """
        Crea un patrón rítmico que respeta la jerarquía métrica.

        PRINCIPIO FUNDAMENTAL (tarea.md líneas 161-166):
        - Notas estructurales en pulsos fuertes
        - Notas de paso en pulsos débiles
        - Cada pulso se trata como una unidad indivisible
        - Las duraciones NO deben cruzar fronteras de pulsos (no síncopas involuntarias)

        Args:
            num_beats: Número de pulsos del patrón (numerador del compás)
        """
        durations = []

        # Iterar pulso por pulso
        for beat_index in range(num_beats):
            is_strong_beat = beat_index in self.strong_beats

            # Determinar cuántos sixteenths tiene este pulso
            # En 4/4: cada pulso = 4 sixteenths
            # En 3/8: cada pulso = 2 sixteenths
            # En 7/8: depende de la subdivisión
            sixteenths_per_beat = 16 // self.meter_tuple[1]

            # Decidir el patrón para este pulso
            beat_durations = self._create_beat_subdivision(
                sixteenths_per_beat, is_strong_beat, beat_index
            )

            durations.extend(beat_durations)

        return RhythmicPattern(
            durations=durations, strong_beat_indices=self.strong_beats
        )

    def _create_beat_subdivision(
        self, sixteenths: int, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """
        Subdivide un pulso en duraciones que NO crucen la frontera del pulso.

        Args:
            sixteenths: Cuántos sixteenths tiene este pulso
            is_strong: Si es un pulso fuerte (acentuado)
            beat_index: Índice del pulso en el compás

        Returns:
            Lista de duraciones (numerador, denominador) que suman exactamente 'sixteenths'
        """
        # En pulsos fuertes: preferir notas largas (para notas estructurales)
        # En pulsos débiles: permitir más subdivisión (para notas de paso)

        if sixteenths == 4:  # Pulso de negra (4/4, 2/4, etc.)
            return self._subdivide_quarter_note_beat(is_strong, beat_index)
        elif sixteenths == 2:  # Pulso de corchea (3/8, 5/8, etc.)
            return self._subdivide_eighth_note_beat(is_strong, beat_index)
        elif sixteenths == 6:  # Pulso de negra con puntillo (6/8, 9/8, 12/8)
            return self._subdivide_dotted_quarter_beat(is_strong, beat_index)
        else:
            # Para otros casos, usar negra simple
            return [(1, 4)]

    def _subdivide_quarter_note_beat(
        self, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """
        Subdivide un pulso de negra (4 sixteenths).

        REGLA: En pulsos fuertes, preferir nota larga (nota estructural)
               En pulsos débiles, permitir subdivisión (notas de paso)
        """
        if self.rhythmic_complexity == 1:  # Simple
            if is_strong or random.random() < 0.7:
                # Pulso fuerte O 70% del tiempo: una negra completa
                return [(1, 4)]
            else:
                # Dos corcheas (subdivisión binaria)
                return [(1, 8), (1, 8)]

        elif self.rhythmic_complexity == 2:  # Moderado
            if is_strong:
                # Pulso fuerte: 80% negra, 20% subdivisión
                if random.random() < 0.8:
                    return [(1, 4)]
                else:
                    return [(1, 8), (1, 8)]
            else:
                # Pulso débil: más variedad
                choice = random.random()
                if choice < 0.4:
                    return [(1, 4)]  # Negra
                elif choice < 0.8:
                    return [(1, 8), (1, 8)]  # Dos corcheas
                else:
                    # Patrón puntillo DENTRO del pulso: corchea puntillo + semicorchea
                    # (3/16 + 1/16 = 4/16 = 1/4)
                    return [(3, 16), (1, 16)]

        else:  # Complejo
            if is_strong:
                # Pulso fuerte: preferir nota larga
                if random.random() < 0.7:
                    return [(1, 4)]
                else:
                    return [(1, 8), (1, 8)]
            else:
                # Pulso débil: máxima variedad
                choice = random.random()
                if choice < 0.3:
                    return [(1, 4)]
                elif choice < 0.5:
                    return [(1, 8), (1, 8)]
                elif choice < 0.7:
                    return [(3, 16), (1, 16)]  # Puntillo + semicorchea
                else:
                    return [(1, 16), (1, 16), (1, 16), (1, 16)]  # Cuatro semicorcheas

    def _subdivide_eighth_note_beat(
        self, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """
        Subdivide un pulso de corchea (2 sixteenths) - usado en 3/8, 5/8, 7/8.
        """
        if is_strong or self.rhythmic_complexity <= 2:
            # Pulso fuerte O complejidad baja: una corchea completa
            return [(1, 8)]
        else:
            # Pulso débil en complejidad alta: dos semicorcheas
            if random.random() < 0.7:
                return [(1, 8)]
            else:
                return [(1, 16), (1, 16)]

    def _subdivide_dotted_quarter_beat(
        self, is_strong: bool, beat_index: int
    ) -> List[Tuple[int, int]]:
        """
        Subdivide un pulso de negra con puntillo (6 sixteenths) - usado en 6/8, 9/8, 12/8.
        """
        if self.rhythmic_complexity == 1:
            # Simple: negra con puntillo o tres corcheas
            if is_strong or random.random() < 0.7:
                return [(3, 8)]  # Negra con puntillo
            else:
                return [(1, 8), (1, 8), (1, 8)]  # Tres corcheas

        elif self.rhythmic_complexity == 2:
            if is_strong:
                if random.random() < 0.8:
                    return [(3, 8)]
                else:
                    return [(1, 8), (1, 8), (1, 8)]
            else:
                choice = random.random()
                if choice < 0.4:
                    return [(3, 8)]
                elif choice < 0.7:
                    return [(1, 8), (1, 8), (1, 8)]
                else:
                    # Corchea + negra (2/16 + 4/16 = 6/16)
                    return [(1, 8), (1, 4)]

        else:  # Complejo
            if is_strong:
                return [(3, 8)] if random.random() < 0.7 else [(1, 8), (1, 8), (1, 8)]
            else:
                choice = random.random()
                if choice < 0.25:
                    return [(3, 8)]
                elif choice < 0.5:
                    return [(1, 8), (1, 8), (1, 8)]
                elif choice < 0.75:
                    return [(1, 8), (1, 4)]
                else:
                    # Seis semicorcheas
                    return [(1, 16)] * 6

    def should_use_rest(
        self,
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        is_phrase_boundary: bool,
    ) -> bool:
        """
        Determina si se debe usar un silencio en este punto.

        Los silencios se usan estratégicamente como:
        - Respiraciones al final de semifrases
        - Impulsos anacrúsicos (antes del tiempo fuerte)
        - Silencios acéfalos (en el tiempo fuerte)
        - Puntos de articulación

        Returns:
            True si se debe usar silencio
        """
        if not self.use_rests:
            return False

        # Evitar dos silencios consecutivos
        if self.last_was_rest:
            return False

        # Nunca silencio en la nota final de una cadencia
        is_final_measure = measure_index == self.num_measures - 1
        is_semifinal_measure = measure_index == (self.num_measures // 2) - 1
        is_last_beat = beat_index >= self.meter_tuple[0] - 1

        if (is_final_measure or is_semifinal_measure) and is_last_beat:
            return False

        # Respiración al final de semifrase (mayor probabilidad)
        if is_phrase_boundary and beat_index == self.meter_tuple[0] - 1:
            return random.random() < self.rest_probability * 2

        # Impulso anacrúsico: silencio antes del tiempo fuerte
        if (
            self.impulse_type == ImpulseType.ANACROUSTIC
            and beat_index == 0
            and measure_index % 2 == 0
        ):
            return random.random() < self.rest_probability * 1.5

        # Silencio acéfalo: silencio en tiempo fuerte
        if (
            self.impulse_type == ImpulseType.ACEPHALOUS
            and is_strong_beat
            and measure_index % 3 == 0
        ):
            return random.random() < self.rest_probability * 1.2

        # Silencios decorativos en tiempos débiles (baja probabilidad)
        if not is_strong_beat:
            return random.random() < self.rest_probability * 0.5

        return False

    def create_base_motif(self, harmonic_function: int = 1) -> Motif:
        """
        Genera el motivo base (célula melódica de 2-4 notas) que será la semilla
        de toda la melodía.

        Este motivo debe ser:
        - Memorable y característico
        - Breve (2-4 notas típicamente)
        - Con un ritmo distintivo
        - Basado en grados estructurales del acorde

        Args:
            harmonic_function: Grado del acorde base (1=I, 4=IV, 5=V)

        Returns:
            Motif con pitches, intervalos, ritmo y grados
        """
        # Generar ritmo característico del motivo (2-4 notas)
        # Longitud: entre 1 y 2 pulsos típicamente
        motif_length_beats = random.choice([1, 2])

        # Crear patrón rítmico para el motivo
        if motif_length_beats == 1:
            # Motivo de 1 pulso: 2-4 notas
            if self.rhythmic_complexity <= 2:
                # Simple: 2 notas (corchea-corchea o negra punteada-corchea)
                durations = [(1, 8), (1, 8)]
            else:
                # Complejo: 3-4 notas
                durations = random.choice(
                    [
                        [(1, 8), (1, 8), (1, 8), (1, 8)],  # 4 corcheas
                        [(1, 8), (3, 16)],  # Corchea + corchea punteada
                        [(3, 16), (1, 16), (1, 8)],  # Sincopado
                    ]
                )
        else:  # 2 pulsos
            # Motivo de 2 pulsos: 2-3 notas
            if self.rhythmic_complexity <= 2:
                durations = [(1, 4), (1, 4)]  # 2 negras
            else:
                durations = random.choice(
                    [
                        [(1, 4), (1, 8), (1, 8)],  # Negra + 2 corcheas
                        [(3, 8), (1, 8)],  # Negra punteada + corchea
                        [(1, 8), (1, 8), (1, 4)],  # 2 corcheas + negra
                    ]
                )

        # Marcar índices de pulsos fuertes
        strong_beat_indices = [0]  # Siempre el primer elemento es fuerte

        rhythm = RhythmicPattern(
            durations=durations, strong_beat_indices=strong_beat_indices
        )

        # Generar grados melódicos del motivo (notas estructurales del acorde)
        chord_tones = self.get_chord_tones_for_function(harmonic_function)

        # El motivo debe tener un contorno característico
        # Opciones: ascendente, descendente, arco, arco invertido
        contour_type = random.choice(
            ["ascending", "descending", "arch", "inverted_arch"]
        )

        num_notes = len(durations)
        degrees = []
        pitches = []
        intervals = []

        # Primera nota: siempre del acorde (preferiblemente tónica o quinta)
        if random.random() < 0.6:
            first_degree = 1 if harmonic_function == 1 else harmonic_function
        else:
            first_degree = random.choice(chord_tones)

        degrees.append(first_degree)
        first_pitch_str = self.get_pitch_by_degree(first_degree)
        pitches.append(first_pitch_str)

        # Generar notas restantes según el contorno
        for i in range(1, num_notes):
            is_last = i == num_notes - 1

            if contour_type == "ascending":
                # Ascender por grado conjunto o tercera
                interval_semitones = random.choice([1, 2, 3, 4])  # m2, M2, m3, M3

            elif contour_type == "descending":
                # Descender por grado conjunto o tercera
                interval_semitones = random.choice([-1, -2, -3, -4])

            elif contour_type == "arch":
                # Subir hasta el medio, luego bajar
                if i <= num_notes // 2:
                    interval_semitones = random.choice([1, 2, 3])
                else:
                    interval_semitones = random.choice([-1, -2, -3])

            else:  # inverted_arch
                # Bajar hasta el medio, luego subir
                if i <= num_notes // 2:
                    interval_semitones = random.choice([-1, -2, -3])
                else:
                    interval_semitones = random.choice([1, 2, 3])

            # Aplicar el intervalo
            prev_pitch = pitch.Pitch(pitches[-1])
            new_pitch = prev_pitch.transpose(interval_semitones)

            # Verificar que esté en el ámbito permitido
            if new_pitch.ps < self.melodic_range_bottom.ps:
                new_pitch = self.melodic_range_bottom.transpose(
                    random.choice([0, 2, 4])
                )
            elif new_pitch.ps > self.melodic_range_top.ps:
                new_pitch = self.melodic_range_top.transpose(random.choice([0, -2, -4]))

            pitches.append(new_pitch.nameWithOctave)
            intervals.append(interval_semitones)

            # Calcular grado de la escala
            degree = self._pitch_to_degree(new_pitch.nameWithOctave)
            degrees.append(degree)

        return Motif(
            pitches=pitches, intervals=intervals, rhythm=rhythm, degrees=degrees
        )

    def create_harmonic_progression(self, num_measures: int) -> List[HarmonicFunction]:
        """
        Crea una progresión armónica implícita para un período de num_measures compases.

        La armonía guía la selección de notas melódicas, creando un contexto tonal coherente.
        Progresión típica: I → IV → V → I (con variaciones)

        Args:
            num_measures: Número de compases del período

        Returns:
            Lista de HarmonicFunction, una por compás
        """
        progression = []

        # Mapeo de grados a nombres de calidad
        if self.mode in ["major", "lydian", "mixolydian"]:
            # Modos mayores
            chord_qualities = {
                1: "major",  # I
                2: "minor",  # ii
                3: "minor",  # iii
                4: "major",  # IV
                5: "major",  # V
                6: "minor",  # vi
                7: "diminished",  # vii°
            }
        else:
            # Modos menores y otros
            chord_qualities = {
                1: "minor",  # i
                2: "diminished",  # ii°
                3: "major",  # III
                4: "minor",  # iv
                5: "minor",  # v (puede ser mayor en armónica)
                6: "major",  # VI
                7: "major",  # VII (puede ser diminuido)
            }

            # Ajuste para menor armónica
            if self.mode == "harmonic_minor":
                chord_qualities[5] = "major"  # V mayor (sensible)
                chord_qualities[7] = "diminished"

        # Niveles de tensión por grado
        tension_levels = {
            1: 0.0,  # Reposo total
            2: 0.4,  # Tensión moderada
            3: 0.3,  # Tensión leve
            4: 0.5,  # Subdominante (preparación)
            5: 0.8,  # Dominante (máxima tensión)
            6: 0.3,  # Relativo menor/mayor
            7: 0.9,  # Sensible (altísima tensión)
        }

        # Generar progresión según longitud
        if num_measures <= 2:
            # Muy corto: solo I-V o I-I
            degrees = [1, 5] if num_measures == 2 else [1]

        elif num_measures <= 4:
            # Semifrase típica: I-IV-V-I o I-I-IV-V
            degrees = [1, 1, 4, 5] if num_measures == 4 else [1, 4, 5]

        elif num_measures <= 8:
            # Período clásico: antecedente (I-IV-V) + consecuente (I-IV-V-I)
            # Compases 1-4 (antecedente):
            antecedent = [1, 1, 4, 5]  # Termina en V (semicadencia)

            # Compases 5-8 (consecuente):
            consequent = [1, 1, 4, 5] if num_measures == 8 else [1, 4, 5]
            # Pero el último debe ser I (cadencia auténtica)
            consequent[-1] = 1

            degrees = antecedent + consequent[: num_measures - 4]

        else:
            # Obra larga: dividir en secciones de 8 compases
            num_periods = (num_measures + 7) // 8  # Redondear hacia arriba
            degrees = []

            for period_idx in range(num_periods):
                # Cada período de 8 compases
                if period_idx < num_periods - 1:
                    # Períodos intermedios
                    degrees.extend([1, 1, 4, 5, 1, 1, 4, 5])
                else:
                    # Último período (puede ser incompleto)
                    remaining = num_measures - len(degrees)
                    if remaining >= 8:
                        degrees.extend([1, 1, 4, 5, 1, 1, 4, 1])
                    elif remaining >= 4:
                        degrees.extend([1, 1, 4, 5])
                        degrees.extend([1] * (remaining - 4))
                    else:
                        degrees.extend([1] * remaining)

            # Ajustar longitud exacta
            degrees = degrees[:num_measures]

            # Asegurar que el último compás sea I (tónica)
            degrees[-1] = 1

        # Convertir grados a HarmonicFunction objects
        for degree in degrees:
            quality = chord_qualities.get(degree, "major")
            tension = tension_levels.get(degree, 0.5)
            chord_tones = self.get_chord_tones_for_function(degree)

            progression.append(
                HarmonicFunction(
                    degree=degree,
                    quality=quality,
                    tension=tension,
                    chord_tones=chord_tones,
                )
            )

        return progression

    def apply_motif_variation(
        self, original_motif: Motif, variation_type: str = "auto"
    ) -> Motif:
        """
        Aplica una variación a un motivo según el nivel de libertad configurado.

        Args:
            original_motif: Motivo original a variar
            variation_type: Tipo de variación ("auto", "strict", "moderate", "free")
                           "auto" usa self.variation_freedom

        Returns:
            Nuevo Motif con la variación aplicada
        """
        if variation_type == "auto":
            freedom = self.variation_freedom
        elif variation_type == "strict":
            freedom = 1
        elif variation_type == "moderate":
            freedom = 2
        elif variation_type == "free":
            freedom = 3
        else:
            freedom = self.variation_freedom

        # Seleccionar tipo de variación según libertad
        if freedom == 1:  # Estricta: variaciones conservadoras
            variation_options = [
                MotivicVariation.ORIGINAL,
                MotivicVariation.RETROGRADE,
                MotivicVariation.TRANSPOSITION,
            ]
            weights = [
                0.4,
                0.3,
                0.3,
            ]  # 40% sin cambio, 30% retrogradación, 30% transposición

        elif freedom == 2:  # Moderada: variaciones clásicas
            variation_options = [
                MotivicVariation.ORIGINAL,
                MotivicVariation.RETROGRADE,
                MotivicVariation.INVERSION,
                MotivicVariation.TRANSPOSITION,
                MotivicVariation.AUGMENTATION,
                MotivicVariation.DIMINUTION,
            ]
            weights = [0.2, 0.2, 0.2, 0.2, 0.1, 0.1]

        else:  # Libre: todas las variaciones posibles
            variation_options = list(MotivicVariation)
            weights = [1 / len(variation_options)] * len(variation_options)

        # Seleccionar variación
        import random

        variation = random.choices(variation_options, weights=weights)[0]

        # Aplicar la variación seleccionada
        if variation == MotivicVariation.ORIGINAL:
            return original_motif

        elif variation == MotivicVariation.RETROGRADE:
            # Invertir el orden de notas y ritmos
            return Motif(
                pitches=list(reversed(original_motif.pitches)),
                intervals=list(reversed([-i for i in original_motif.intervals])),
                rhythm=RhythmicPattern(
                    durations=list(reversed(original_motif.rhythm.durations)),
                    strong_beat_indices=original_motif.rhythm.strong_beat_indices,
                ),
                degrees=list(reversed(original_motif.degrees)),
            )

        elif variation == MotivicVariation.INVERSION:
            # Invertir los intervalos (subir → bajar, bajar → subir)
            new_pitches = [original_motif.pitches[0]]  # Primera nota igual
            new_degrees = [original_motif.degrees[0]]
            new_intervals = []

            for interval_semi in original_motif.intervals:
                # Invertir el intervalo
                inverted_interval = -interval_semi
                new_intervals.append(inverted_interval)

                # Aplicar a la última nota
                prev_pitch = pitch.Pitch(new_pitches[-1])
                new_pitch = prev_pitch.transpose(inverted_interval)

                # Verificar ámbito
                if new_pitch.ps < self.melodic_range_bottom.ps:
                    new_pitch = self.melodic_range_bottom.transpose(
                        random.choice([0, 2, 4])
                    )
                elif new_pitch.ps > self.melodic_range_top.ps:
                    new_pitch = self.melodic_range_top.transpose(
                        random.choice([0, -2, -4])
                    )

                new_pitches.append(new_pitch.nameWithOctave)
                new_degrees.append(self._pitch_to_degree(new_pitch.nameWithOctave))

            return Motif(
                pitches=new_pitches,
                intervals=new_intervals,
                rhythm=original_motif.rhythm,
                degrees=new_degrees,
            )

        elif variation == MotivicVariation.TRANSPOSITION:
            # Transponer el motivo a otro grado
            transposition_steps = random.choice([-2, -1, 1, 2])  # Por grado conjunto
            new_pitches = []
            new_degrees = []

            for p_str in original_motif.pitches:
                p = pitch.Pitch(p_str)
                new_p = p.transpose(transposition_steps)

                # Verificar ámbito
                if new_p.ps < self.melodic_range_bottom.ps:
                    new_p = new_p.transpose(12)  # Subir octava
                elif new_p.ps > self.melodic_range_top.ps:
                    new_p = new_p.transpose(-12)  # Bajar octava

                new_pitches.append(new_p.nameWithOctave)
                new_degrees.append(self._pitch_to_degree(new_p.nameWithOctave))

            return Motif(
                pitches=new_pitches,
                intervals=original_motif.intervals,  # Intervalos se mantienen
                rhythm=original_motif.rhythm,
                degrees=new_degrees,
            )

        elif variation == MotivicVariation.AUGMENTATION:
            # Aumentar duraciones rítmicas (×2)
            augmented_durations = []
            for num, denom in original_motif.rhythm.durations:
                # Doblar la duración: (1,8) → (1,4), (1,4) → (1,2)
                new_denom = max(1, denom // 2)
                augmented_durations.append((num, new_denom))

            return Motif(
                pitches=original_motif.pitches,
                intervals=original_motif.intervals,
                rhythm=RhythmicPattern(
                    durations=augmented_durations,
                    strong_beat_indices=original_motif.rhythm.strong_beat_indices,
                ),
                degrees=original_motif.degrees,
            )

        elif variation == MotivicVariation.DIMINUTION:
            # Disminuir duraciones rítmicas (÷2)
            diminished_durations = []
            for num, denom in original_motif.rhythm.durations:
                # Reducir a la mitad: (1,4) → (1,8), (1,2) → (1,4)
                new_denom = min(32, denom * 2)
                diminished_durations.append((num, new_denom))

            return Motif(
                pitches=original_motif.pitches,
                intervals=original_motif.intervals,
                rhythm=RhythmicPattern(
                    durations=diminished_durations,
                    strong_beat_indices=original_motif.rhythm.strong_beat_indices,
                ),
                degrees=original_motif.degrees,
            )

        else:
            # Para SEQUENCE, RETROGRADE_INVERSION: por ahora retornar original
            # Se pueden implementar después
            return original_motif

    def select_melodic_pitch(
        self,
        measure_index: int,
        beat_index: int,
        is_strong_beat: bool,
        rhythm_pattern: RhythmicPattern,
        note_index_in_measure: int,
    ) -> Tuple[str, NoteFunction]:
        """
        Selecciona el tono melódico según las reglas de la teoría musical.

        Returns:
            Tupla de (nota, función)
        """
        harmonic_function = self.get_harmonic_function(measure_index, beat_index)
        chord_tones = self.get_chord_tones_for_function(harmonic_function)

        # Determinar si debe ser nota estructural
        should_be_structural = is_strong_beat

        # Sistema de infracción
        if (
            random.random() < self.infraction_rate
            and not self.infraction_pending_compensation
        ):
            should_be_structural = not should_be_structural
            self.infraction_pending_compensation = True
        elif self.infraction_pending_compensation:
            should_be_structural = True
            self.infraction_pending_compensation = False

        # Considerar tenoris (quinta como nota sostenedora)
        use_tenoris_now = (
            self.use_tenoris
            and should_be_structural
            and random.random() < self.tenoris_probability
            and not is_strong_beat  # No en tiempos muy fuertes
        )

        if use_tenoris_now:
            # Usar quinta como nota sostenedora (tenoris gregoriano)
            degree = 5
            function = NoteFunction.STRUCTURAL
        elif should_be_structural:
            # Nota estructural: del acorde
            degree = random.choice(chord_tones)
            function = NoteFunction.STRUCTURAL
        else:
            # Nota de paso o bordadura (siempre por grado conjunto)
            if self.last_pitch:
                # Movimiento por grado conjunto (segunda mayor/menor)
                last_degree = self._pitch_to_degree(self.last_pitch)
                if random.random() < 0.5:
                    degree = last_degree + 1 if last_degree < 7 else 1
                else:
                    degree = last_degree - 1 if last_degree > 1 else 7
                function = NoteFunction.PASSING
            else:
                degree = 2  # Nota de paso por defecto
                function = NoteFunction.PASSING

        # Ajustar octava para mantener contorno controlado
        note_pitch = self.get_pitch_by_degree(degree)

        # Control de rango y clímax
        if self.last_pitch:
            note_pitch = self._adjust_octave_for_contour(
                note_pitch, measure_index, is_structural=should_be_structural
            )

        self.last_pitch = note_pitch
        return note_pitch, function

    def _pitch_to_degree(self, pitch_str: str) -> int:
        """Convierte un pitch string a grado de escala."""
        p = pitch.Pitch(pitch_str)
        for deg in range(1, 8):
            scale_pitch = self.scale.pitchFromDegree(deg)
            if p.name == scale_pitch.name:
                return deg
        return 1

    def _convert_to_abjad_pitch(self, pitch_str: str) -> str:
        """
        Convierte un pitch de music21 a formato estándar LilyPond.

        Args:
            pitch_str: String de pitch en formato music21 (ej: "c4", "c#4", "eb5")

        Returns:
            String de pitch en formato LilyPond estándar
            - Sostenidos: 'is' (c# → cis, f# → fis)
            - Bemoles: 'es' (eb → ees, bb → bes)
            - Octavas: c' = C4, c'' = C5, c = C3, c, = C2
        """
        p = pitch.Pitch(pitch_str)

        # Obtener nombre base (c, d, e, f, g, a, b)
        base_name = p.step.lower()

        # Convertir alteración a formato Abjad (English notation for Note creation)
        alteration = p.alter
        if alteration == 0:
            # Natural
            accidental_suffix = ""
        elif alteration == 1:
            # Sostenido: +s (sharp)
            accidental_suffix = "s"
        elif alteration == -1:
            # Bemol: +f (flat)
            accidental_suffix = "f"
        elif alteration == 2:
            # Doble sostenido: +ss
            accidental_suffix = "ss"
        elif alteration == -2:
            # Doble bemol: +ff
            accidental_suffix = "ff"
        else:
            # Alteraciones microtonales o inusuales
            if alteration > 0:
                accidental_suffix = "s" * int(abs(alteration))
            else:
                accidental_suffix = "f" * int(abs(alteration))

        # Construir nombre completo de la nota
        note_name = f"{base_name}{accidental_suffix}"

        # Calcular marca de octava
        octave = p.octave
        if octave == 3:
            octave_mark = ""
        elif octave < 3:
            octave_mark = "," * (3 - octave)
        else:
            octave_mark = "'" * (octave - 3)

        return f"{note_name}{octave_mark}"

    def _adjust_octave_for_contour(
        self, new_pitch: str, measure_index: int = 0, is_structural: bool = True
    ) -> str:
        """
        Ajusta la octava de una nota para mantener un contorno melódico apropiado.
        Implementa reglas teóricas:
        - Saltos máximo de sexta (preferible quinta/cuarta)
        - Recuperación de saltos por movimiento contrario
        - Ámbito melódico: octava de la tónica ± cuarta
        - Saltos de octava solo en puntos estructurales
        """
        if not self.last_pitch:
            # Primera nota: establecer en rango apropiado
            new_p = pitch.Pitch(new_pitch)
            # Buscar octava que esté dentro del ámbito melódico
            for test_octave in [3, 4, 5]:
                test_p = pitch.Pitch(f"{new_p.name}{test_octave}")
                if (
                    self.melodic_range_bottom.ps
                    <= test_p.ps
                    <= self.melodic_range_top.ps
                ):
                    return f"{new_p.name}{test_octave}"
            return new_pitch

        last_p = pitch.Pitch(self.last_pitch)
        new_p = pitch.Pitch(new_pitch)

        # Calcular influencia del clímax
        climax_factor = self.calculate_climax_influence(measure_index)

        # Si debemos recuperar un salto, forzar movimiento contrario por grado conjunto
        if self.must_recover_leap and self.last_interval_direction is not None:
            # Buscar octava que genere movimiento contrario y pequeño
            best_octave = new_p.octave
            best_interval = 100

            for octave_adj in [-1, 0, 1]:
                test_octave = new_p.octave + octave_adj
                test_p = pitch.Pitch(f"{new_p.name}{test_octave}")

                # Verificar ámbito
                if (
                    test_p.ps < self.melodic_range_bottom.ps
                    or test_p.ps > self.melodic_range_top.ps
                ):
                    continue

                intv = interval.Interval(last_p, test_p)
                intv_semitones = intv.semitones
                intv_size = abs(intv_semitones)

                # Debe ser movimiento contrario (dirección opuesta)
                current_direction = (
                    1 if intv_semitones > 0 else -1 if intv_semitones < 0 else 0
                )

                if (
                    current_direction != 0
                    and current_direction != self.last_interval_direction
                ):
                    # Es movimiento contrario, preferir grado conjunto (2 semitonos o menos)
                    if intv_size <= 2 and intv_size < best_interval:
                        best_interval = intv_size
                        best_octave = test_octave

            if best_interval < 100:
                result = f"{new_p.name}{best_octave}"
                result_p = pitch.Pitch(result)
                intv = interval.Interval(last_p, result_p)
                self.last_interval_direction = (
                    1 if intv.semitones > 0 else -1 if intv.semitones < 0 else 0
                )
                self.must_recover_leap = False  # Salto recuperado
                # Debug: uncomment to see leap recovery in action
                # print(f"  → Leap recovered by {abs(intv.semitones)} semitones (contrary motion)", file=sys.stderr)
                return result

        # Búsqueda normal de octava óptima
        best_octave = new_p.octave
        best_interval_size = 100

        for octave_adj in [-1, 0, 1, 2]:
            test_octave = new_p.octave + octave_adj
            test_p = pitch.Pitch(f"{new_p.name}{test_octave}")

            # Verificar ámbito melódico
            if (
                test_p.ps < self.melodic_range_bottom.ps
                or test_p.ps > self.melodic_range_top.ps
            ):
                continue

            intv = interval.Interval(last_p, test_p)
            intv_semitones = abs(intv.semitones)

            # Aplicar restricciones de salto
            max_allowed = self.max_interval  # Por defecto sexta (9 semitonos)

            # Permitir octava solo en puntos estructurales (tiempos fuertes)
            if is_structural and measure_index == self.climax_measure:
                max_allowed = 12  # Octava permitida en clímax estructural
            elif intv_semitones > 9:  # Más de sexta
                continue  # Rechazar

            # Verificar que no exceda máximo
            if intv_semitones > max_allowed:
                continue

            # Preferir intervalos pequeños (grado conjunto = 1-2 semitonos)
            # Penalizar saltos grandes
            score = intv_semitones
            if intv_semitones <= 2:  # Grado conjunto
                score -= 10  # Bonus grande
            elif intv_semitones <= 5:  # Tercera/cuarta
                score -= 5  # Bonus moderado

            if score < best_interval_size:
                best_interval_size = score
                best_octave = test_octave

        result = f"{new_p.name}{best_octave}"
        result_p = pitch.Pitch(result)

        # Actualizar tracking de intervalos
        intv = interval.Interval(last_p, result_p)
        intv_semitones = intv.semitones
        intv_size = abs(intv_semitones)

        # Si es salto grande (más de tercera), marcar para recuperación
        if intv_size > 4:  # Más de tercera mayor
            self.must_recover_leap = True
            self.last_interval_direction = 1 if intv_semitones > 0 else -1
            # Debug: uncomment to see leap recovery in action
            # print(f"  → Leap detected: {intv_size} semitones, direction: {self.last_interval_direction}", file=sys.stderr)
        else:
            self.last_interval_direction = (
                1 if intv_semitones > 0 else -1 if intv_semitones < 0 else 0
            )

        # Actualizar registro más alto alcanzado
        if (
            self.current_highest_pitch is None
            or result_p.ps > pitch.Pitch(self.current_highest_pitch).ps
        ):
            self.current_highest_pitch = result
            if measure_index == self.climax_measure:
                self.climax_reached = True

        return result

    def create_measure(
        self,
        measure_index: int,
        is_cadence: bool = False,
        cadence_type: str = "authentic",
    ) -> abjad.Container:
        """
        Crea un compás basado en la estructura de pulsos fuertes y la teoría armónica.
        Garantiza que las duraciones sumen exactamente el quarterLength del compás.

        Args:
            measure_index: Índice del compás en la pieza
            is_cadence: Si este compás contiene una cadencia
            cadence_type: "authentic" (V-I) o "half" (I-V o II-V)
        """
        notes = []

        # MEJORA: Usar motivo rítmico base con variaciones para cohesión
        rhythm_pattern = self._get_rhythmic_pattern_with_variation(measure_index)

        # Iterar por cada duración en el patrón rítmico
        current_position = Fraction(0)  # Posición en quarterLength
        total_ql = Fraction(self.meter_tuple[0], self.meter_tuple[1]) * 4

        for note_index, duration in enumerate(rhythm_pattern.durations):
            # Calcular quarterLength de esta duración
            duration_ql = Fraction(duration[0], duration[1]) * 4

            # Determinar si estamos en tiempo fuerte
            # Convertir current_position a beats
            beat_position = current_position * self.meter_tuple[1] / 4
            is_strong = int(beat_position) in self.strong_beats

            # Determinar si es límite de semifrase
            # Estamos cerca del final del compás?
            is_near_end = (current_position + duration_ql) >= (total_ql * 0.9)
            is_phrase_boundary = is_near_end and measure_index % 2 == 1

            # Verificar si debemos usar silencio
            # Convertir beat_position a int para compatibilidad
            beat_index_int = int(beat_position)
            use_rest = self.should_use_rest(
                measure_index, beat_index_int, is_strong, is_phrase_boundary
            )

            if use_rest:
                # Crear silencio con soporte para puntillo
                if duration[0] == 3:
                    # Silencio con puntillo (misma lógica que notas)
                    if duration[1] == 8:
                        base_duration = 4
                    elif duration[1] == 16:
                        base_duration = 8
                    elif duration[1] == 4:
                        base_duration = 2
                    elif duration[1] == 32:
                        base_duration = 16
                    elif duration[1] == 2:
                        base_duration = 1
                    else:
                        base_duration = duration[1]
                    rest_string = f"r{base_duration}."
                elif duration[0] == 1:
                    rest_string = f"r{duration[1]}"
                else:
                    rest_string = f"r{duration[1]}"

                rest = abjad.Rest(rest_string)
                notes.append(rest)
                self.last_was_rest = True
            else:
                # Lógica especial para cadencias
                # Usar is_near_end para detectar si estamos en cadencia
                if is_cadence and is_near_end:
                    # Estamos en las últimas notas del compás cadencial
                    is_penultimate = note_index == len(rhythm_pattern.durations) - 2
                    is_final = note_index == len(rhythm_pattern.durations) - 1

                    if cadence_type == "authentic":
                        # V -> I (cadencia auténtica)
                        if is_penultimate:
                            note_pitch = self.get_pitch_by_degree(7)  # Sensible (VII)
                        elif is_final:
                            note_pitch = self.get_pitch_by_degree(1)  # Tónica
                        else:
                            note_pitch, _ = self.select_melodic_pitch(
                                measure_index,
                                beat_index_int,
                                is_strong,
                                rhythm_pattern,
                                note_index,
                            )
                    elif cadence_type == "half":
                        # Semicadencia (termina en V)
                        if is_final:
                            note_pitch = self.get_pitch_by_degree(5)  # Dominante
                        elif is_penultimate:
                            note_pitch = self.get_pitch_by_degree(4)  # Subdominante
                        else:
                            note_pitch, _ = self.select_melodic_pitch(
                                measure_index,
                                beat_index_int,
                                is_strong,
                                rhythm_pattern,
                                note_index,
                            )
                    else:
                        note_pitch, _ = self.select_melodic_pitch(
                            measure_index,
                            beat_index_int,
                            is_strong,
                            rhythm_pattern,
                            note_index,
                        )
                else:
                    note_pitch, _ = self.select_melodic_pitch(
                        measure_index,
                        beat_index_int,
                        is_strong,
                        rhythm_pattern,
                        note_index,
                    )

                # Convertir pitch a formato Abjad (ej: "c4" → "c'", "c5" → "c''")
                abjad_pitch = self._convert_to_abjad_pitch(note_pitch)

                # Crear string en formato Abjad: "pitch + duration" (ej: "c'4")
                # Para duraciones con numerador > 1, usar punto para notas con puntillo
                if duration[0] == 3:
                    # Duracion con puntillo: (3, denom) → (2*denom/3).
                    # Ej: (3, 8) = 3/8 = dotted quarter = "4."  porque 2*8/3 = 16/3 ≈ 5.33 pero redondeamos
                    # Mejor manera: (3, 8) → base_lily = 2 * 8 / 3 = 16/3... pero necesitamos entero
                    # Patrón correcto:
                    # (3, 8) → 4. (dotted quarter)
                    # (3, 16) → 8. (dotted eighth)
                    # (3, 4) → 2. (dotted half)
                    # Formula: base_lily = (2 * denom) / 3
                    if duration[1] == 8:
                        base_duration = 4
                    elif duration[1] == 16:
                        base_duration = 8
                    elif duration[1] == 4:
                        base_duration = 2
                    elif duration[1] == 32:
                        base_duration = 16
                    elif duration[1] == 2:
                        base_duration = 1
                    else:
                        base_duration = duration[1]
                    note_string = f"{abjad_pitch}{base_duration}."
                elif duration[0] == 1:
                    note_string = f"{abjad_pitch}{duration[1]}"
                else:
                    # Para otras duraciones complejas, crear múltiples notas ligadas
                    # Por ahora simplificamos a la duración base
                    note_string = f"{abjad_pitch}{duration[1]}"

                note = abjad.Note(note_string)
                notes.append(note)
                self.last_was_rest = False

            # Incrementar posición actual
            current_position += duration_ql

        return abjad.Container(notes)

    def _add_ties_to_staff(self, staff: abjad.Staff, tie_probability: float = 0.15):
        """
        Añade ligaduras (ties) entre notas del mismo pitch con probabilidad controlada.
        Respeta reglas de teoría musical:
        - No ligar sobre cadencias (últimos 2 beats de compases cadenciales)
        - No ligar desde/hacia silencios
        - Mayor probabilidad en tiempos débiles
        - No ligar si rompe la claridad rítmica

        Args:
            staff: El Staff de Abjad con las notas
            tie_probability: Probabilidad base de añadir tie (0.0-1.0)
        """
        # Obtener todas las hojas (notes y rests) del staff
        all_leaves = list(abjad.select.leaves(staff))

        midpoint = self.num_measures // 2

        for i in range(len(all_leaves) - 1):
            current_leaf = all_leaves[i]
            next_leaf = all_leaves[i + 1]

            # Solo procesar notas (no silencios)
            if not isinstance(current_leaf, abjad.Note) or not isinstance(
                next_leaf, abjad.Note
            ):
                continue

            # Verificar que sean la misma nota (mismo pitch)
            if current_leaf.written_pitch != next_leaf.written_pitch:
                continue

            # Determinar contexto musical
            # Encontrar en qué compás estamos
            measure_idx = None
            for m_idx, container in enumerate(staff):
                if current_leaf in container:
                    measure_idx = m_idx
                    break

            if measure_idx is None:
                continue

            # No ligar en cadencias (compases con cadencias)
            is_antecedent_end = measure_idx == midpoint - 1
            is_period_end = measure_idx == self.num_measures - 1

            if is_antecedent_end or is_period_end:
                # En compases cadenciales, no ligar los últimos beats
                container = staff[measure_idx]
                note_position = list(container).index(current_leaf)
                if note_position >= len(container) - 2:
                    continue

            # Aplicar probabilidad
            # Aumentar probabilidad si son notas largas (quarters o mayores)
            duration_multiplier = 1.0
            if (
                current_leaf.written_duration.numerator >= 1
                and current_leaf.written_duration.denominator <= 4
            ):
                duration_multiplier = 1.5

            effective_probability = tie_probability * duration_multiplier

            if random.random() < effective_probability:
                # Añadir tie
                abjad.attach(abjad.Tie(), current_leaf)

    def generate_period(self) -> abjad.Staff:
        """
        Genera un período musical completo (Antecedente + Consecuente).
        Implementa la estructura de pregunta-respuesta con cadencias apropiadas.

        MEJORA: Genera un motivo rítmico base que se reutiliza para cohesión.
        """
        staff = abjad.Staff(name="Melodia")

        # NUEVO: Generar motivo rítmico base (se reutiliza en toda la pieza)
        # Esto crea cohesión melódica según tarea.md: "economía de materiales"
        self.base_rhythmic_motif = self.create_rhythmic_pattern(self.meter_tuple[0])

        midpoint = self.num_measures // 2

        for m_idx in range(self.num_measures):
            # Determinar tipo de cadencia
            is_antecedent_end = m_idx == midpoint - 1
            is_period_end = m_idx == self.num_measures - 1

            if is_period_end:
                # Cadencia auténtica al final del consecuente
                container = self.create_measure(
                    m_idx, is_cadence=True, cadence_type="authentic"
                )
            elif is_antecedent_end:
                # Semicadencia al final del antecedente
                container = self.create_measure(
                    m_idx, is_cadence=True, cadence_type="half"
                )
            else:
                container = self.create_measure(m_idx, is_cadence=False)

            # Agregar el container al staff
            staff.append(container)

            # Añadir barline después de cada compás (excepto el último)
            if m_idx < self.num_measures - 1:
                last_leaf = abjad.get.leaf(container, -1)
                if last_leaf:
                    abjad.attach(abjad.BarLine("|"), last_leaf)
            else:
                # Barline final al último compás
                last_leaf = abjad.get.leaf(container, -1)
                if last_leaf:
                    abjad.attach(abjad.BarLine("|."), last_leaf)

        # Añadir indicaciones al inicio
        if len(staff) > 0 and len(staff[0]) > 0:
            abjad.attach(abjad.TimeSignature(self.meter_tuple), staff[0][0])
            abjad.attach(abjad.Clef("treble"), staff[0][0])

            # Añadir armadura de clave
            key_sig = self._create_key_signature()
            if key_sig:
                abjad.attach(key_sig, staff[0][0])

        # Añadir ligaduras (ties) con probabilidad controlada
        self._add_ties_to_staff(staff, tie_probability=0.15)

        return staff

    def generate_period_hierarchical(self) -> abjad.Staff:
        """
        NUEVO MÉTODO: Genera un período musical con jerarquía formal verdadera.

        Implementa la estructura:
        Motivo → Frase (2 compases) → Semifrase (4 compases) → Período (8+ compases)

        Este método coexiste con generate_period() para permitir comparación.

        Estructura para 8 compases:
        - Compases 1-2: Frase 1 (motivo + variación dramática)
        - Compases 3-4: Frase 2 (desarrollo del motivo + semicadencia)
        - Compases 5-6: Frase 3 (retorno al motivo + desarrollo)
        - Compases 7-8: Frase 4 (preparación + cadencia auténtica)

        Returns:
            abjad.Staff con la melodía generada jerárquicamente
        """
        staff = abjad.Staff(name="Melodia_Hierarchical")

        # 1. Crear progresión armónica para toda la obra
        harmonic_progression = self.create_harmonic_progression(self.num_measures)

        # 2. Generar motivo base (basado en la armonía del compás 1)
        base_motif = self.create_base_motif(harmonic_progression[0].degree)

        # 3. Determinar estructura de frases
        # Cada frase = 2 compases (motivo + respuesta)
        num_phrases = (self.num_measures + 1) // 2

        # 4. Generar cada frase
        for phrase_idx in range(num_phrases):
            measure_start = phrase_idx * 2
            measure_end = min(measure_start + 2, self.num_measures)

            # Determinar tipo de variación según posición en el período
            if phrase_idx == 0:
                # Primera frase: presentar motivo original + variación dramática
                variation_types = ["auto", "auto"]  # Según variation_freedom

            elif measure_end == self.num_measures // 2:
                # Final del antecedente: preparar semicadencia
                variation_types = ["auto", "strict"]  # Más conservador

            elif phrase_idx == num_phrases - 1:
                # Última frase: cadencia auténtica
                variation_types = ["strict", "strict"]  # Muy conservador

            else:
                # Frases intermedias: desarrollo libre
                variation_types = ["auto", "auto"]

            # Generar los 2 compases de esta frase
            for local_measure_idx in range(measure_end - measure_start):
                global_measure_idx = measure_start + local_measure_idx

                if global_measure_idx >= self.num_measures:
                    break

                # Determinar si este compás usa el motivo original o variación
                if local_measure_idx == 0:
                    # Primer compás de la frase: motivo (posiblemente variado)
                    if phrase_idx == 0:
                        # Primera frase: motivo puro
                        current_motif = base_motif
                    else:
                        # Frases posteriores: aplicar variación según contexto
                        current_motif = self.apply_motif_variation(
                            base_motif, variation_type=variation_types[0]
                        )
                else:
                    # Segundo compás de la frase: respuesta/variación
                    current_motif = self.apply_motif_variation(
                        base_motif, variation_type=variation_types[1]
                    )

                # Obtener función armónica para este compás
                harmonic_func = harmonic_progression[global_measure_idx]

                # Generar el compás basado en el motivo y la armonía
                measure_container = self._create_measure_from_motif(
                    current_motif, harmonic_func, global_measure_idx
                )

                staff.append(measure_container)

                # Agregar barline
                if global_measure_idx < self.num_measures - 1:
                    last_leaf = abjad.get.leaf(measure_container, -1)
                    if last_leaf:
                        abjad.attach(abjad.BarLine("|"), last_leaf)
                else:
                    # Barline final
                    last_leaf = abjad.get.leaf(measure_container, -1)
                    if last_leaf:
                        abjad.attach(abjad.BarLine("|."), last_leaf)

        # Añadir indicaciones al inicio
        if len(staff) > 0 and len(staff[0]) > 0:
            abjad.attach(abjad.TimeSignature(self.meter_tuple), staff[0][0])
            abjad.attach(abjad.Clef("treble"), staff[0][0])

            # Añadir armadura de clave
            key_sig = self._create_key_signature()
            if key_sig:
                abjad.attach(key_sig, staff[0][0])

        return staff

    def _create_measure_from_motif(
        self, motif: Motif, harmonic_func: HarmonicFunction, measure_index: int
    ) -> abjad.Container:
        """
        Crea un compás a partir de un motivo y una función armónica.

        Args:
            motif: Motivo a usar como base
            harmonic_func: Función armónica del compás
            measure_index: Índice del compás en el período

        Returns:
            abjad.Container con las notas del compás
        """
        notes = []

        # El motivo puede no llenar el compás completo
        # Calcular duración del motivo
        motif_duration_ql = sum(
            Fraction(num, denom) * 4  # Convertir a quarter notes
            for num, denom in motif.rhythm.durations
        )

        measure_duration_ql = Fraction(self.meter_tuple[0], self.meter_tuple[1]) * 4

        # Si el motivo no llena el compás, completar con notas adicionales
        # basadas en la armonía
        current_position = Fraction(0)

        # Primero agregar las notas del motivo
        for idx, (pitch_str, duration) in enumerate(
            zip(motif.pitches, motif.rhythm.durations)
        ):
            # Convertir pitch a formato Abjad
            abjad_pitch = self._convert_to_abjad_pitch(pitch_str)

            # Crear duración en formato Abjad
            if duration[0] == 3:
                # Nota con puntillo
                if duration[1] == 8:
                    base_duration = 4
                elif duration[1] == 16:
                    base_duration = 8
                elif duration[1] == 4:
                    base_duration = 2
                elif duration[1] == 32:
                    base_duration = 16
                elif duration[1] == 2:
                    base_duration = 1
                else:
                    base_duration = duration[1]
                note_string = f"{abjad_pitch}{base_duration}."
            elif duration[0] == 1:
                note_string = f"{abjad_pitch}{duration[1]}"
            else:
                note_string = f"{abjad_pitch}{duration[1]}"

            note = abjad.Note(note_string)
            notes.append(note)

            current_position += Fraction(duration[0], duration[1]) * 4

        # Completar el compás si es necesario
        remaining_duration = measure_duration_ql - current_position

        while remaining_duration > 0:
            # Seleccionar una nota del acorde para completar
            degree = random.choice(harmonic_func.chord_tones)
            pitch_str = self.get_pitch_by_degree(degree)
            abjad_pitch = self._convert_to_abjad_pitch(pitch_str)

            # Determinar duración para completar
            if remaining_duration >= 1:  # Quarter note o más
                duration_denom = 4
            elif remaining_duration >= Fraction(1, 2):  # Eighth note
                duration_denom = 8
            else:  # Sixteenth note
                duration_denom = 16

            note_string = f"{abjad_pitch}{duration_denom}"
            note = abjad.Note(note_string)
            notes.append(note)

            remaining_duration -= Fraction(1, duration_denom) * 4

        return abjad.Container(notes)

    def _create_key_signature(self):
        """
        Crea un objeto KeySignature de Abjad basado en self.k (music21 Key).

        Returns:
            abjad.KeySignature object o None si no se puede determinar
        """
        # Obtener tónica de la tonalidad (self.k es un objeto key.Key de music21)
        tonic = self.k.tonic

        # Convertir nombre de la tónica a formato LilyPond (solo pitch class, sin octava)
        # music21 usa "C", "D-", "E#", etc. - convertir a LilyPond "c", "des", "eis", etc.
        base_name = tonic.step.lower()  # c, d, e, f, g, a, b

        # Convertir alteración
        alteration = tonic.alter
        if alteration == 0:
            accidental_suffix = ""
        elif alteration == 1:
            accidental_suffix = "is"
        elif alteration == -1:
            # Bemol con contracciones
            if base_name == "a":
                accidental_suffix = "s"  # as (A-flat)
            elif base_name == "e":
                accidental_suffix = "s"  # es (E-flat)
            else:
                accidental_suffix = "es"  # ces, des, fes, ges, bes
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

        # Determinar modo desde self.mode (el parámetro del constructor)
        # LilyPond solo soporta modos diatónicos, otros se mapean al más cercano
        mode_name = self.mode.lower()
        if mode_name in ["major", "ionian"]:
            mode_lily = "major"
        elif mode_name in ["minor", "aeolian"]:
            mode_lily = "minor"
        elif mode_name == "dorian":
            mode_lily = "dorian"
        elif mode_name == "phrygian":
            mode_lily = "phrygian"
        elif mode_name == "lydian":
            mode_lily = "lydian"
        elif mode_name == "mixolydian":
            mode_lily = "mixolydian"
        elif mode_name == "locrian":
            mode_lily = "locrian"
        # Escalas menores -> usar minor como base
        elif mode_name in ["harmonic_minor", "melodic_minor"]:
            mode_lily = "minor"
        # Modos de menor armónica -> mapear a equivalentes cercanos
        elif mode_name == "locrian_nat6":
            mode_lily = "locrian"
        elif mode_name == "ionian_aug5":
            mode_lily = "major"
        elif mode_name == "dorian_sharp4":
            mode_lily = "dorian"
        elif mode_name == "phrygian_dominant":
            mode_lily = "phrygian"
        elif mode_name == "lydian_sharp2":
            mode_lily = "lydian"
        elif mode_name == "superlocrian_bb7":
            mode_lily = "locrian"
        # Modos de menor melódica -> mapear a equivalentes cercanos
        elif mode_name == "dorian_flat2":
            mode_lily = "dorian"
        elif mode_name == "lydian_augmented":
            mode_lily = "lydian"
        elif mode_name == "lydian_dominant":
            mode_lily = "lydian"
        elif mode_name == "mixolydian_flat6":
            mode_lily = "mixolydian"
        elif mode_name == "locrian_nat2":
            mode_lily = "locrian"
        elif mode_name == "altered":
            mode_lily = "locrian"
        else:
            # Por defecto usar major
            mode_lily = "major"

        try:
            return abjad.KeySignature(
                abjad.NamedPitchClass(tonic_name), abjad.Mode(mode_lily)
            )
        except:
            # Si falla, intentar con formato alternativo
            return None

    def _english_to_standard_pitch(self, english_pitch: str) -> str:
        """
        Convierte notación inglesa de Abjad (bf, cs) a notación estándar LilyPond (bes, cis).

        Args:
            english_pitch: Pitch en notación inglesa (ej: "bf", "cs", "c")

        Returns:
            Pitch en notación estándar (ej: "bes", "cis", "c")
        """
        # Separar nota base de alteraciones y octavas
        base = english_pitch[0]  # Primera letra (c, d, e, f, g, a, b)
        rest = english_pitch[1:]  # Resto (alteraciones + octavas)

        # Extraer alteraciones (antes de ' o ,)
        accidental = ""
        octave = ""

        for char in rest:
            if char in ["'", ","]:
                octave += char
            else:
                accidental += char

        # Convertir alteración de inglés a estándar
        if not accidental:
            standard_accidental = ""
        elif accidental == "s":  # sharp → is
            standard_accidental = "is"
        elif accidental == "ss":  # double sharp → isis
            standard_accidental = "isis"
        elif accidental == "f":  # flat → es (con contracciones)
            if base == "a":
                standard_accidental = "s"  # as
            elif base == "e":
                standard_accidental = "s"  # es
            else:
                standard_accidental = "es"  # bes, ces, des, fes, ges
        elif accidental == "ff":  # double flat → eses (con contracciones)
            if base in ["a", "e"]:
                standard_accidental = "ses"  # ases, eses
            else:
                standard_accidental = "eses"  # beses, etc.
        else:
            # Si no reconocemos, mantener original
            standard_accidental = accidental

        return f"{base}{standard_accidental}{octave}"

    def _to_absolute_lilypond(self, staff: abjad.Staff) -> str:
        """
        Convierte un Staff de Abjad a código LilyPond con notación absoluta.
        Formato profesional sin bloques por compás.

        Returns:
            String con código LilyPond usando notación absoluta
        """
        # Obtener todas las hojas (notas y silencios)
        leaves = list(abjad.select.leaves(staff))

        if not leaves:
            return "{ }"

        # Construir lista de elementos con formato LilyPond
        lily_elements = []

        for i, leaf in enumerate(leaves):
            if isinstance(leaf, abjad.Note):
                # Obtener pitch y duración (llamar a los métodos)
                pitch_obj = leaf.written_pitch()
                # Usar el formato LilyPond nativo (inglés) y convertir a estándar
                pitch_str_english = pitch_obj._get_lilypond_format()
                pitch_str = self._english_to_standard_pitch(pitch_str_english)
                duration_obj = leaf.written_duration()

                # Convertir duración de Abjad a LilyPond
                numerator = duration_obj.numerator
                denominator = duration_obj.denominator

                if numerator == 1:
                    lily_duration = str(denominator)
                elif numerator == 3:
                    # Nota con puntillo - usar tabla de conversión
                    dotted_map = {
                        2: "1",  # 3/2 = dotted whole
                        4: "2",  # 3/4 = dotted half
                        8: "4",  # 3/8 = dotted quarter
                        16: "8",  # 3/16 = dotted eighth
                        32: "16",  # 3/32 = dotted sixteenth
                        64: "32",  # 3/64 = dotted 32nd
                    }
                    lily_duration = dotted_map.get(denominator, str(denominator)) + "."
                else:
                    # Otros casos: usar denominador
                    lily_duration = str(denominator)

                lily_elements.append(f"{pitch_str}{lily_duration}")

            elif isinstance(leaf, abjad.Rest):
                # Silencio
                duration_obj = leaf.written_duration()
                numerator = duration_obj.numerator
                denominator = duration_obj.denominator

                if numerator == 1:
                    lily_duration = str(denominator)
                elif numerator == 3:
                    # Silencio con puntillo - misma tabla de conversión
                    dotted_map = {2: "1", 4: "2", 8: "4", 16: "8", 32: "16", 64: "32"}
                    lily_duration = dotted_map.get(denominator, str(denominator)) + "."
                else:
                    lily_duration = str(denominator)

                lily_elements.append(f"r{lily_duration}")

            # Añadir barlines si están attached
            indicators = abjad.get.indicators(leaf)
            for indicator in indicators:
                if isinstance(indicator, abjad.BarLine):
                    # Usar | simple para verificación, excepto barline final
                    if indicator.abbreviation == "|.":
                        lily_elements.append('\\bar "|."')
                    else:
                        lily_elements.append("|")

        # Formatear con saltos de línea cada 4-6 elementos (un compás aprox)
        output_lines = []
        current_line = []
        elements_per_line = 6

        for elem in lily_elements:
            current_line.append(elem)
            # Nueva línea después de cada compás (marcado por | o \bar)
            if len(current_line) >= elements_per_line or "\\bar" in elem or elem == "|":
                output_lines.append(" ".join(current_line))
                current_line = []

        if current_line:
            output_lines.append(" ".join(current_line))

        # Construir código final
        formatted_code = "\n    ".join(output_lines)

        return f"{{\n    {formatted_code}\n  }}"

    def generate_and_display(
        self, output_format: str = "lilypond", title: str = None, composer: str = None
    ) -> str:
        """
        Genera el período y retorna la representación en formato LilyPond profesional.

        Args:
            output_format: "lilypond" para código LilyPond, "show" para visualizar
            title: Título opcional de la pieza
            composer: Compositor opcional
        """
        partitura = self.generate_period()

        if output_format == "show":
            abjad.show(partitura)
            return "Partitura mostrada"
        else:
            # Obtener información de armadura y compás
            key_sig_str = self._get_key_signature_string()
            time_sig = f"\\time {self.meter_tuple[0]}/{self.meter_tuple[1]}"
            clef = '\\clef "treble"'
            strict_beaming = "\\set strictBeatBeaming = ##t"

            # Generar código con notación absoluta
            music_code = self._to_absolute_lilypond(partitura)

            # Construir salida completa
            output = ""

            # Header opcional
            if title or composer:
                output += "\\header {\n"
                if title:
                    output += f'  title = "{title}"\n'
                if composer:
                    output += f'  composer = "{composer}"\n'
                output += "}\n\n"

            # Score
            output += "\\score {\n"

            # Insertar music_code con indicaciones al inicio
            lines = music_code.split("\n")
            # Insertar time, key, clef, strictBeatBeaming después de la primera {
            if len(lines) > 1:
                lines[1] = (
                    f"    {time_sig}\n    {key_sig_str}\n    {clef}\n    {strict_beaming}\n{lines[1]}"
                )
            output += "\n".join(lines)

            output += "\n\n  \\layout {}\n"
            output += "  \\midi {}\n"
            output += "}\n"

            return output

    def _get_key_signature_string(self) -> str:
        """Retorna la armadura de clave como string LilyPond."""
        tonic = self.k.tonic
        base_name = tonic.step.lower()

        # Convertir alteración (usar notación estándar LilyPond para \key)
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

        # Modo (LilyPond solo soporta modos diatónicos)
        mode_name = self.mode.lower()
        if mode_name in ["major", "ionian"]:
            mode_lily = "\\major"
        elif mode_name in ["minor", "aeolian"]:
            mode_lily = "\\minor"
        elif mode_name == "dorian":
            mode_lily = "\\dorian"
        elif mode_name == "phrygian":
            mode_lily = "\\phrygian"
        elif mode_name == "lydian":
            mode_lily = "\\lydian"
        elif mode_name == "mixolydian":
            mode_lily = "\\mixolydian"
        elif mode_name == "locrian":
            mode_lily = "\\locrian"
        # Escalas menores -> usar minor como base
        elif mode_name in ["harmonic_minor", "melodic_minor"]:
            mode_lily = "\\minor"
        # Modos de menor armónica -> mapear a equivalentes cercanos
        elif mode_name == "locrian_nat6":
            mode_lily = "\\locrian"
        elif mode_name == "ionian_aug5":
            mode_lily = "\\major"
        elif mode_name == "dorian_sharp4":
            mode_lily = "\\dorian"
        elif mode_name == "phrygian_dominant":
            mode_lily = "\\phrygian"
        elif mode_name == "lydian_sharp2":
            mode_lily = "\\lydian"
        elif mode_name == "superlocrian_bb7":
            mode_lily = "\\locrian"
        # Modos de menor melódica -> mapear a equivalentes cercanos
        elif mode_name == "dorian_flat2":
            mode_lily = "\\dorian"
        elif mode_name == "lydian_augmented":
            mode_lily = "\\lydian"
        elif mode_name == "lydian_dominant":
            mode_lily = "\\lydian"
        elif mode_name == "mixolydian_flat6":
            mode_lily = "\\mixolydian"
        elif mode_name == "locrian_nat2":
            mode_lily = "\\locrian"
        elif mode_name == "altered":
            mode_lily = "\\locrian"
        else:
            mode_lily = "\\major"

        return f"\\key {tonic_name} {mode_lily}"


def main():
    """Función principal interactiva."""

    print("=" * 70)
    print("GENERADOR DE MELODÍAS - PROTOCOLO SYMMETRY & LOGIC")
    print("=" * 70)
    print()
    print("Este programa genera melodías basadas en teoría musical clásica.")
    print()

    # Solicitar parámetros al usuario
    print("=== CONFIGURACIÓN DE LA MELODÍA ===")
    print()

    # Tonalidad
    key_name = input("Tonalidad (ej: C, D, Eb, F#) [C]: ").strip() or "C"

    # Modo
    print("\nModos disponibles:")
    print("\n--- MODOS DIATÓNICOS (de escala mayor) ---")
    print("1. major (Jónico / Mayor)")
    print("2. dorian (Dórico)")
    print("3. phrygian (Frigio)")
    print("4. lydian (Lidio)")
    print("5. mixolydian (Mixolidio)")
    print("6. minor (Aeolian / Menor natural)")
    print("7. locrian (Locrio)")

    print("\n--- ESCALAS MENORES ---")
    print("8. harmonic_minor (Menor armónica)")
    print("9. melodic_minor (Menor melódica)")

    print("\n--- MODOS DE MENOR ARMÓNICA ---")
    print("10. locrian_nat6 (Locrio ♮6)")
    print("11. ionian_aug5 (Jónico aumentado)")
    print("12. dorian_sharp4 (Dórico #4 / Ucraniano)")
    print("13. phrygian_dominant (Frigio dominante / Frigio mayor)")
    print("14. lydian_sharp2 (Lidio #2)")
    print("15. superlocrian_bb7 (Ultralocrio)")

    print("\n--- MODOS DE MENOR MELÓDICA ---")
    print("16. dorian_flat2 (Dórico ♭2 / Frigio #6)")
    print("17. lydian_augmented (Lidio aumentado)")
    print("18. lydian_dominant (Lidio dominante / Mixolidio #4)")
    print("19. mixolydian_flat6 (Mixolidio ♭6)")
    print("20. locrian_nat2 (Locrio ♮2 / Semilocrio)")
    print("21. altered (Alterado / Superlocrio)")

    mode_choice = input("\nSeleccione modo [1]: ").strip() or "1"
    mode_map = {
        # Diatónicos
        "1": "major",
        "2": "dorian",
        "3": "phrygian",
        "4": "lydian",
        "5": "mixolydian",
        "6": "minor",
        "7": "locrian",
        # Menores
        "8": "harmonic_minor",
        "9": "melodic_minor",
        # Menor armónica
        "10": "locrian_nat6",
        "11": "ionian_aug5",
        "12": "dorian_sharp4",
        "13": "phrygian_dominant",
        "14": "lydian_sharp2",
        "15": "superlocrian_bb7",
        # Menor melódica
        "16": "dorian_flat2",
        "17": "lydian_augmented",
        "18": "lydian_dominant",
        "19": "mixolydian_flat6",
        "20": "locrian_nat2",
        "21": "altered",
    }
    mode = mode_map.get(mode_choice, "major")

    # Compás
    print("\nCompás:")
    numerator = int(input("  Numerador (pulsos por compás) [4]: ").strip() or "4")
    denominator = int(input("  Denominador (figura que cuenta) [4]: ").strip() or "4")
    meter_tuple = (numerator, denominator)

    # Subdivisiones para métricas amalgama
    subdivisions = None
    if numerator in [5, 7, 11]:
        print(f"\nMétrica amalgama detectada ({numerator}/{denominator})")
        print(f"¿Cómo subdividir los {numerator} pulsos?")
        if numerator == 5:
            subdiv_input = input("  Ej: 2+3 o 3+2 [2+3]: ").strip() or "2+3"
        elif numerator == 7:
            subdiv_input = input("  Ej: 2+2+3 o 3+2+2 [2+2+3]: ").strip() or "2+2+3"
        else:
            subdiv_input = input(
                f"  Separados por + (deben sumar {numerator}): "
            ).strip()

        subdivisions = [int(x) for x in subdiv_input.split("+")]

    # Número de compases
    num_measures = int(input("\nNúmero de compases [8]: ").strip() or "8")

    # Tipo de impulso
    print("\nTipo de impulso:")
    print("1. Tético (comienza en tiempo fuerte)")
    print("2. Anacrúsico (comienza antes del tiempo fuerte)")
    print("3. Acéfalo (comienza después del tiempo fuerte)")
    impulse_choice = input("Seleccione [1]: ").strip() or "1"
    impulse_map = {
        "1": ImpulseType.TETIC,
        "2": ImpulseType.ANACROUSTIC,
        "3": ImpulseType.ACEPHALOUS,
    }
    impulse_type = impulse_map.get(impulse_choice, ImpulseType.TETIC)

    # Complejidad rítmica
    print("\nComplejidad rítmica:")
    print("1. Simple (negras y corcheas)")
    print("2. Moderado (incluye puntillos)")
    print("3. Complejo (semicorcheas y subdivisiones)")
    complexity = int(input("Seleccione [2]: ").strip() or "2")

    # Usar silencios
    use_rests_input = (
        input("\n¿Usar silencios como respiraciones? (s/n) [s]: ").strip().lower()
        or "s"
    )
    use_rests = use_rests_input == "s"

    # Usar tenoris
    use_tenoris_input = (
        input("¿Usar 'tenoris' (quinta como nota sostenedora)? (s/n) [n]: ")
        .strip()
        .lower()
        or "n"
    )
    use_tenoris = use_tenoris_input == "s"

    # Posición del clímax
    climax_input = input("\nPosición del clímax (0.0-1.0) [0.75]: ").strip()
    climax_pos = float(climax_input) if climax_input else 0.75

    # Libertad de variación (NUEVO)
    print("\nLibertad de variación motívica:")
    print("1. Estricta (motivo muy reconocible, variaciones conservadoras)")
    print("2. Moderada (equilibrio entre familiaridad y novedad)")
    print("3. Libre (máxima libertad creativa)")
    variation_freedom_input = input("Seleccione nivel [2]: ").strip() or "2"
    variation_freedom = (
        int(variation_freedom_input)
        if variation_freedom_input in ["1", "2", "3"]
        else 2
    )

    # Tipo de generación (NUEVO)
    print("\nMétodo de generación:")
    print("1. Tradicional (sistema actual, cohesión rítmica)")
    print("2. Jerárquico (NUEVO: Motivo → Frase → Semifrase → Período)")
    generation_method_input = input("Seleccione método [1]: ").strip() or "1"
    use_hierarchical = generation_method_input == "2"

    # Título y compositor
    print("\n=== INFORMACIÓN DE LA PARTITURA ===")
    title = input("Título [Melodía Generada]: ").strip() or "Melodía Generada"
    composer = (
        input("Compositor [MelodicArchitect AI]: ").strip() or "MelodicArchitect AI"
    )

    print("\n" + "=" * 70)
    print("Generando melodía...")
    print("=" * 70)
    print()

    # Crear arquitecto con los parámetros del usuario
    try:
        architect = MelodicArchitect(
            key_name=key_name,
            mode=mode,
            meter_tuple=meter_tuple,
            subdivisions=subdivisions,
            num_measures=num_measures,
            impulse_type=impulse_type,
            infraction_rate=0.1,  # Valor balanceado
            rhythmic_complexity=complexity,
            use_rests=use_rests,
            rest_probability=0.15,
            use_motivic_variations=True,
            variation_probability=0.4,
            climax_position=climax_pos,
            climax_intensity=1.5,
            max_interval=6,  # Máximo sexta
            use_tenoris=use_tenoris,
            tenoris_probability=0.2,
            variation_freedom=variation_freedom,  # NUEVO
        )

        # Generar melodía según el método seleccionado
        if use_hierarchical:
            print("Usando método JERÁRQUICO (Motivo → Frase → Semifrase → Período)")
            staff = architect.generate_period_hierarchical()
            lilypond_code = architect.generate_and_display(
                title=title, composer=composer
            )
            # Reemplazar el staff generado con el jerárquico
            # (por ahora usamos el método tradicional para el output,
            # pero en el futuro se puede adaptar)
        else:
            print("Usando método TRADICIONAL (cohesión rítmica)")
            lilypond_code = architect.generate_and_display(
                title=title, composer=composer
            )

        print(lilypond_code)
        print()
        print("=" * 70)
        print("¡Melodía generada exitosamente!")
        print("=" * 70)

        # Opción de guardar en archivo
        save_option = (
            input("\n¿Guardar en archivo .ly? (s/n) [n]: ").strip().lower() or "n"
        )
        if save_option == "s":
            # Sanitizar el título para usar como nombre de archivo
            import re

            safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
            default_filename = f"{safe_title}.ly" if safe_title else "melodia.ly"
            filename = (
                input(f"Nombre del archivo [{default_filename}]: ").strip()
                or default_filename
            )

            # Asegurar extensión .ly
            if not filename.endswith(".ly"):
                filename += ".ly"

            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(lilypond_code)
                print(f"✓ Archivo guardado: {filename}")
                print(f"  Puede abrirlo con: lilypond {filename}")
                print(f"  O en Frescobaldi para edición visual")
            except Exception as e:
                print(f"✗ Error al guardar archivo: {e}")
        else:
            print("Copie el código LilyPond anterior y péguelo en Frescobaldi")
            print("o guárdelo manualmente en un archivo .ly para compilarlo.")

        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error al generar la melodía: {e}")
        print("Por favor, verifique los parámetros ingresados.")


if __name__ == "__main__":
    main()
