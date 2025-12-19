"""
Ornamentación melódica.
Implementa ornamentos estilísticos: appoggiaturas, mordentes, trinos, grupetos.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
import random


class OrnamentType(Enum):
    """Tipos de ornamento."""
    APPOGGIATURA = "appoggiatura"      # Nota de ataque disonante
    ACCIACCATURA = "acciaccatura"      # Appoggiatura corta (grace note)
    MORDENT = "mordent"                 # Mordente (nota-vecina-nota)
    INVERTED_MORDENT = "inv_mordent"   # Mordente invertido
    TRILL = "trill"                     # Trino
    TURN = "turn"                       # Grupeto
    PASSING_CHROMATIC = "chromatic"    # Nota de paso cromática


class OrnamentStyle(Enum):
    """Estilos de ornamentación."""
    BAROQUE = "baroque"      # Estilo barroco (muchos ornamentos)
    CLASSICAL = "classical"  # Estilo clásico (ornamentos moderados)
    ROMANTIC = "romantic"    # Estilo romántico (expresivo)
    MINIMAL = "minimal"      # Mínimo (solo esenciales)
    NONE = "none"           # Sin ornamentos


@dataclass
class Ornament:
    """Representa un ornamento aplicado a una nota."""
    ornament_type: OrnamentType
    main_pitch: str          # Nota principal
    auxiliary_pitches: List[str]  # Notas auxiliares del ornamento
    durations: List[Tuple[int, int]]  # Duraciones de cada nota
    position: str = "before"  # "before", "on", "after" el beat


@dataclass
class OrnamentConfig:
    """Configuración para ornamentación."""
    style: OrnamentStyle = OrnamentStyle.CLASSICAL
    appoggiatura_probability: float = 0.15
    mordent_probability: float = 0.10
    trill_probability: float = 0.08
    turn_probability: float = 0.05
    chromatic_probability: float = 0.05
    # Solo en cadencias
    cadential_trill: bool = True
    # Preferir ornamentos en tiempos débiles
    prefer_weak_beats: bool = True


class OrnamentGenerator:
    """
    Genera ornamentos melódicos según el estilo.

    Los ornamentos añaden expresividad y carácter estilístico
    a la melodía generada.
    """

    def __init__(
        self,
        config: OrnamentConfig = None,
        scale_pitches: List[str] = None,
    ):
        """
        Inicializa el generador de ornamentos.

        Args:
            config: Configuración de ornamentación
            scale_pitches: Notas de la escala (para ornamentos diatónicos)
        """
        self.config = config or OrnamentConfig()
        self.scale_pitches = scale_pitches or []

        # Ajustar probabilidades según estilo
        self._adjust_for_style()

    def _adjust_for_style(self):
        """Ajusta probabilidades según el estilo seleccionado."""
        style = self.config.style

        if style == OrnamentStyle.BAROQUE:
            self.config.appoggiatura_probability = 0.20
            self.config.mordent_probability = 0.15
            self.config.trill_probability = 0.12
            self.config.turn_probability = 0.08
        elif style == OrnamentStyle.CLASSICAL:
            self.config.appoggiatura_probability = 0.12
            self.config.mordent_probability = 0.08
            self.config.trill_probability = 0.06
            self.config.turn_probability = 0.04
        elif style == OrnamentStyle.ROMANTIC:
            self.config.appoggiatura_probability = 0.18
            self.config.mordent_probability = 0.05
            self.config.trill_probability = 0.10
            self.config.chromatic_probability = 0.10
        elif style == OrnamentStyle.MINIMAL:
            self.config.appoggiatura_probability = 0.05
            self.config.mordent_probability = 0.03
            self.config.trill_probability = 0.02
            self.config.turn_probability = 0.01
        elif style == OrnamentStyle.NONE:
            self.config.appoggiatura_probability = 0.0
            self.config.mordent_probability = 0.0
            self.config.trill_probability = 0.0
            self.config.turn_probability = 0.0

    def should_ornament(
        self,
        is_strong_beat: bool,
        is_cadence: bool,
        note_duration: Tuple[int, int],
        phrase_position: float,
    ) -> Optional[OrnamentType]:
        """
        Determina si una nota debe ser ornamentada y con qué tipo.

        Args:
            is_strong_beat: Si es tiempo fuerte
            is_cadence: Si estamos en cadencia
            note_duration: Duración de la nota
            phrase_position: Posición en la frase (0.0-1.0)

        Returns:
            Tipo de ornamento o None
        """
        if self.config.style == OrnamentStyle.NONE:
            return None

        # Notas muy cortas no se ornamentan
        if note_duration[1] >= 16:  # Semicorchea o más corta
            return None

        # Trino cadencial
        if is_cadence and self.config.cadential_trill:
            if note_duration[1] <= 4:  # Negra o más larga
                if random.random() < 0.7:  # Alta probabilidad en cadencias
                    return OrnamentType.TRILL

        # Preferir tiempos débiles (excepto appoggiaturas)
        beat_modifier = 0.7 if is_strong_beat and self.config.prefer_weak_beats else 1.0

        # Evaluar cada tipo de ornamento
        if random.random() < self.config.appoggiatura_probability:
            return OrnamentType.APPOGGIATURA

        if random.random() < self.config.mordent_probability * beat_modifier:
            return OrnamentType.MORDENT

        if random.random() < self.config.trill_probability * beat_modifier:
            if note_duration[1] <= 4:  # Solo en notas largas
                return OrnamentType.TRILL

        if random.random() < self.config.turn_probability * beat_modifier:
            return OrnamentType.TURN

        if random.random() < self.config.chromatic_probability:
            return OrnamentType.PASSING_CHROMATIC

        return None

    def create_appoggiatura(
        self,
        main_pitch: str,
        from_above: bool = True,
        duration: Tuple[int, int] = (1, 8),
    ) -> Ornament:
        """
        Crea una appoggiatura.

        La appoggiatura es una nota disonante que resuelve por grado
        conjunto a la nota principal, típicamente desde arriba.

        Args:
            main_pitch: Nota principal de resolución
            from_above: Si viene desde arriba (más común)
            duration: Duración de la appoggiatura
        """
        # Calcular nota auxiliar (un grado arriba o abajo)
        aux_pitch = self._get_neighbor_pitch(main_pitch, upper=from_above)

        return Ornament(
            ornament_type=OrnamentType.APPOGGIATURA,
            main_pitch=main_pitch,
            auxiliary_pitches=[aux_pitch],
            durations=[duration],
            position="on",  # La appoggiatura cae en el beat
        )

    def create_acciaccatura(
        self,
        main_pitch: str,
        from_above: bool = True,
    ) -> Ornament:
        """
        Crea una acciaccatura (grace note corta).

        Similar a la appoggiatura pero sin valor rítmico real.
        """
        aux_pitch = self._get_neighbor_pitch(main_pitch, upper=from_above)

        return Ornament(
            ornament_type=OrnamentType.ACCIACCATURA,
            main_pitch=main_pitch,
            auxiliary_pitches=[aux_pitch],
            durations=[(1, 16)],  # Muy corta
            position="before",
        )

    def create_mordent(
        self,
        main_pitch: str,
        inverted: bool = False,
    ) -> Ornament:
        """
        Crea un mordente.

        Mordente normal: nota-nota superior-nota
        Mordente invertido: nota-nota inferior-nota

        Args:
            main_pitch: Nota principal
            inverted: Si es mordente invertido
        """
        aux_pitch = self._get_neighbor_pitch(main_pitch, upper=not inverted)

        return Ornament(
            ornament_type=OrnamentType.INVERTED_MORDENT if inverted else OrnamentType.MORDENT,
            main_pitch=main_pitch,
            auxiliary_pitches=[aux_pitch],
            durations=[(1, 32), (1, 32)],  # Rápido
            position="on",
        )

    def create_trill(
        self,
        main_pitch: str,
        total_duration: Tuple[int, int],
        with_termination: bool = True,
    ) -> Ornament:
        """
        Crea un trino.

        El trino alterna rápidamente entre la nota y su vecina superior.

        Args:
            main_pitch: Nota principal
            total_duration: Duración total del trino
            with_termination: Si incluir terminación (2 notas finales)
        """
        aux_pitch = self._get_neighbor_pitch(main_pitch, upper=True)

        # Calcular número de alternancias basado en duración
        base_unit = (1, 32)
        num_alternations = (total_duration[0] * 32) // total_duration[1]
        num_alternations = max(4, num_alternations)  # Mínimo 4

        auxiliary_pitches = []
        durations = []

        for i in range(num_alternations):
            if i % 2 == 0:
                auxiliary_pitches.append(main_pitch)
            else:
                auxiliary_pitches.append(aux_pitch)
            durations.append(base_unit)

        # Terminación opcional
        if with_termination and len(auxiliary_pitches) >= 2:
            lower_pitch = self._get_neighbor_pitch(main_pitch, upper=False)
            auxiliary_pitches[-2] = lower_pitch
            auxiliary_pitches[-1] = main_pitch

        return Ornament(
            ornament_type=OrnamentType.TRILL,
            main_pitch=main_pitch,
            auxiliary_pitches=auxiliary_pitches,
            durations=durations,
            position="on",
        )

    def create_turn(
        self,
        main_pitch: str,
        inverted: bool = False,
    ) -> Ornament:
        """
        Crea un grupeto (turn).

        Grupeto normal: nota-superior-nota-inferior-nota
        Grupeto invertido: nota-inferior-nota-superior-nota

        Args:
            main_pitch: Nota principal
            inverted: Si es grupeto invertido
        """
        upper = self._get_neighbor_pitch(main_pitch, upper=True)
        lower = self._get_neighbor_pitch(main_pitch, upper=False)

        if inverted:
            sequence = [main_pitch, lower, main_pitch, upper, main_pitch]
        else:
            sequence = [main_pitch, upper, main_pitch, lower, main_pitch]

        return Ornament(
            ornament_type=OrnamentType.TURN,
            main_pitch=main_pitch,
            auxiliary_pitches=sequence[1:],  # Excluir primera (es la principal)
            durations=[(1, 32)] * 4,
            position="on",
        )

    def create_chromatic_passing(
        self,
        from_pitch: str,
        to_pitch: str,
    ) -> Ornament:
        """
        Crea una nota de paso cromática entre dos notas.

        Args:
            from_pitch: Nota de origen
            to_pitch: Nota de destino
        """
        # Calcular nota cromática intermedia
        chromatic = self._get_chromatic_between(from_pitch, to_pitch)

        if chromatic:
            return Ornament(
                ornament_type=OrnamentType.PASSING_CHROMATIC,
                main_pitch=to_pitch,
                auxiliary_pitches=[chromatic],
                durations=[(1, 16)],
                position="before",
            )
        return None

    def _get_neighbor_pitch(self, pitch: str, upper: bool = True) -> str:
        """
        Obtiene la nota vecina (diatónica) de una nota.

        Args:
            pitch: Nota base
            upper: Si buscar vecina superior

        Returns:
            Nota vecina diatónica
        """
        # Extraer nombre y octava
        from music21 import pitch as m21_pitch

        try:
            p = m21_pitch.Pitch(pitch)
            semitones = 2 if upper else -2  # Segunda mayor aproximada
            neighbor = p.transpose(semitones)
            return neighbor.nameWithOctave
        except Exception:
            # Fallback simple
            return pitch

    def _get_chromatic_between(
        self,
        from_pitch: str,
        to_pitch: str,
    ) -> Optional[str]:
        """
        Obtiene una nota cromática entre dos notas.

        Returns:
            Nota cromática o None si no es posible
        """
        from music21 import pitch as m21_pitch

        try:
            p1 = m21_pitch.Pitch(from_pitch)
            p2 = m21_pitch.Pitch(to_pitch)

            interval = p2.midi - p1.midi

            if abs(interval) >= 2:
                # Hay espacio para nota cromática
                direction = 1 if interval > 0 else -1
                chromatic = p1.transpose(direction)
                return chromatic.nameWithOctave
        except Exception:
            pass

        return None

    def get_lilypond_ornament_mark(self, ornament_type: OrnamentType) -> str:
        """
        Retorna la marca LilyPond para un ornamento.

        Args:
            ornament_type: Tipo de ornamento

        Returns:
            Comando LilyPond para el ornamento
        """
        marks = {
            OrnamentType.TRILL: "\\trill",
            OrnamentType.MORDENT: "\\mordent",
            OrnamentType.INVERTED_MORDENT: "\\prall",
            OrnamentType.TURN: "\\turn",
            OrnamentType.APPOGGIATURA: "",  # Se escribe como nota
            OrnamentType.ACCIACCATURA: "",  # Se escribe como grace note
            OrnamentType.PASSING_CHROMATIC: "",
        }
        return marks.get(ornament_type, "")


def apply_ornaments_to_notes(
    notes: List[dict],  # Lista de {pitch, duration, is_strong, is_cadence, position}
    generator: OrnamentGenerator,
) -> List[dict]:
    """
    Aplica ornamentos a una lista de notas.

    Args:
        notes: Lista de diccionarios con información de notas
        generator: Generador de ornamentos

    Returns:
        Lista modificada con ornamentos insertados
    """
    result = []

    for i, note in enumerate(notes):
        ornament_type = generator.should_ornament(
            is_strong_beat=note.get('is_strong', False),
            is_cadence=note.get('is_cadence', False),
            note_duration=note.get('duration', (1, 4)),
            phrase_position=note.get('position', 0.5),
        )

        if ornament_type:
            ornament = None

            if ornament_type == OrnamentType.APPOGGIATURA:
                ornament = generator.create_appoggiatura(note['pitch'])
            elif ornament_type == OrnamentType.MORDENT:
                ornament = generator.create_mordent(note['pitch'])
            elif ornament_type == OrnamentType.TRILL:
                ornament = generator.create_trill(
                    note['pitch'],
                    note.get('duration', (1, 4))
                )
            elif ornament_type == OrnamentType.TURN:
                ornament = generator.create_turn(note['pitch'])

            if ornament:
                note['ornament'] = ornament

        result.append(note)

    return result


def apply_ornaments_to_staff(
    staff,  # abjad.Staff
    generator: OrnamentGenerator,
    num_measures: int = 8,
) -> None:
    """
    Aplica ornamentos directamente a un staff de Abjad.

    Args:
        staff: Staff de Abjad
        generator: Generador de ornamentos configurado
        num_measures: Número de compases para calcular posición
    """
    import abjad

    leaves = list(abjad.select.leaves(staff))
    notes = [l for l in leaves if isinstance(l, abjad.Note)]

    if not notes:
        return

    notes_per_measure = max(1, len(notes) // num_measures)

    for i, note in enumerate(notes):
        # Calcular posición en la frase (0.0 - 1.0)
        phrase_position = (i % (notes_per_measure * 4)) / (notes_per_measure * 4)

        # Determinar si es tiempo fuerte
        is_strong_beat = (i % notes_per_measure) == 0

        # Determinar si es cadencia
        measure_idx = i // notes_per_measure
        is_cadence = (measure_idx + 1) % 4 == 0 and (i % notes_per_measure) >= notes_per_measure - 2

        # Obtener duración
        dur = note.written_duration()
        duration = (dur.numerator, dur.denominator)

        # Decidir si aplicar ornamento
        ornament_type = generator.should_ornament(
            is_strong_beat=is_strong_beat,
            is_cadence=is_cadence,
            note_duration=duration,
            phrase_position=phrase_position,
        )

        if ornament_type:
            # Aplicar marca de ornamento según tipo
            if ornament_type == OrnamentType.TRILL:
                abjad.attach(abjad.LilyPondLiteral("\\trill", site="after"), note)
            elif ornament_type == OrnamentType.MORDENT:
                abjad.attach(abjad.LilyPondLiteral("\\mordent", site="after"), note)
            elif ornament_type == OrnamentType.INVERTED_MORDENT:
                abjad.attach(abjad.LilyPondLiteral("\\prall", site="after"), note)
            elif ornament_type == OrnamentType.TURN:
                abjad.attach(abjad.LilyPondLiteral("\\turn", site="after"), note)
            elif ornament_type == OrnamentType.APPOGGIATURA:
                # Para appoggiatura, añadir grace note antes
                try:
                    pitch = note.written_pitch()
                    neighbor = pitch.transpose(2)  # Segunda mayor arriba
                    neighbor_str = neighbor._get_lilypond_format()
                    grace_note = abjad.Note(f"{neighbor_str}8")
                    grace = abjad.BeforeGraceContainer([grace_note])
                    abjad.attach(grace, note)
                except Exception:
                    pass  # Si falla, continuar sin grace note
            elif ornament_type == OrnamentType.ACCIACCATURA:
                # Acciaccatura (grace note con slash)
                try:
                    pitch = note.written_pitch()
                    neighbor = pitch.transpose(2)
                    neighbor_str = neighbor._get_lilypond_format()
                    grace_note = abjad.Note(f"{neighbor_str}16")
                    grace = abjad.BeforeGraceContainer([grace_note])
                    abjad.attach(grace, note)
                except Exception:
                    pass
