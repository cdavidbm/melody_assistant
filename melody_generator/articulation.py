"""
Articulaciones automáticas basadas en contexto musical.
Genera staccato, legato, acentos, tenuto según patrones melódicos.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum


class ArticulationType(Enum):
    """Tipos de articulación."""
    STACCATO = "staccato"           # Corto, separado
    STACCATISSIMO = "staccatissimo" # Muy corto
    TENUTO = "tenuto"               # Sostenido, full value
    ACCENT = "accent"               # Énfasis
    MARCATO = "marcato"             # Fuertemente acentuado
    PORTATO = "portato"             # Staccato + legato
    FERMATA = "fermata"             # Pausa
    BREATH = "breath"               # Marca de respiración


@dataclass
class ArticulationMark:
    """Marca de articulación en una nota."""
    position: int
    articulation: ArticulationType


@dataclass
class SlurMark:
    """Marca de ligadura de expresión (slur)."""
    start_position: int
    end_position: int


class ArticulationGenerator:
    """
    Genera articulaciones automáticas según el contexto.

    Reglas generales:
    - Saltos grandes: staccato o acento
    - Grados conjuntos rápidos: legato (slur)
    - Notas largas en tiempo fuerte: tenuto
    - Finales de frase: respiración
    - Notas repetidas: staccato
    """

    def __init__(
        self,
        style: str = "classical",
        staccato_probability: float = 0.3,
        accent_probability: float = 0.2,
    ):
        """
        Inicializa el generador.

        Args:
            style: "baroque", "classical", "romantic"
            staccato_probability: Probabilidad de staccato en saltos
            accent_probability: Probabilidad de acentos
        """
        self.style = style
        self.staccato_probability = staccato_probability
        self.accent_probability = accent_probability

        # Ajustar por estilo
        if style == "baroque":
            self.prefer_detached = True
            self.slur_length = 2  # Slurs cortos
        elif style == "romantic":
            self.prefer_detached = False
            self.slur_length = 8  # Slurs largos
        else:
            self.prefer_detached = False
            self.slur_length = 4

    def analyze_interval(
        self,
        interval_semitones: int,
    ) -> Optional[ArticulationType]:
        """
        Sugiere articulación basada en el intervalo.

        Args:
            interval_semitones: Intervalo en semitonos (puede ser negativo)

        Returns:
            Tipo de articulación sugerida o None
        """
        abs_interval = abs(interval_semitones)

        if abs_interval == 0:
            # Nota repetida: staccato
            return ArticulationType.STACCATO
        elif abs_interval <= 2:
            # Grado conjunto: sin articulación especial (legato implícito)
            return None
        elif abs_interval <= 4:
            # Tercera: posible portato
            return ArticulationType.PORTATO if self.prefer_detached else None
        elif abs_interval <= 7:
            # Cuarta a quinta: staccato o acento
            return ArticulationType.STACCATO
        else:
            # Sexta o mayor: definitivamente marcado
            return ArticulationType.ACCENT

    def generate_articulations(
        self,
        pitches: List[str],
        durations: List[Tuple[int, int]],
        strong_beats: List[bool],
        is_cadence: List[bool],
    ) -> List[ArticulationMark]:
        """
        Genera articulaciones para una secuencia de notas.

        Args:
            pitches: Lista de pitches (strings)
            durations: Lista de duraciones
            strong_beats: Lista de si cada nota está en tiempo fuerte
            is_cadence: Lista de si cada nota está en cadencia

        Returns:
            Lista de marcas de articulación
        """
        import random
        from music21 import pitch as m21_pitch

        marks = []

        for i in range(len(pitches)):
            articulation = None

            # Calcular intervalo con nota anterior
            if i > 0:
                try:
                    p1 = m21_pitch.Pitch(pitches[i-1])
                    p2 = m21_pitch.Pitch(pitches[i])
                    interval = int(p2.midi - p1.midi)
                    articulation = self.analyze_interval(interval)
                except Exception:
                    pass

            # Notas cortas (corcheas o menores) tienen probabilidad de staccato
            if durations[i][1] >= 8 and not articulation:
                if random.random() < self.staccato_probability:
                    articulation = ArticulationType.STACCATO

            # Tiempos fuertes tienen probabilidad de accent
            if strong_beats[i] and not articulation:
                if random.random() < self.accent_probability:
                    articulation = ArticulationType.ACCENT
                elif durations[i][1] <= 4:  # Negra o más larga
                    articulation = ArticulationType.TENUTO

            # Notas largas en tiempo fuerte: tenuto
            if strong_beats[i] and durations[i][1] <= 4:  # Negra o más larga
                if not articulation:
                    articulation = ArticulationType.TENUTO

            # Cadencias: posible fermata en penúltima
            if i > 0 and is_cadence[i] and i == len(pitches) - 2:
                if durations[i][1] <= 2:  # Blanca o más larga
                    articulation = ArticulationType.FERMATA

            # Última nota de frase: respiración después
            if i == len(pitches) - 1 and len(pitches) > 4:
                marks.append(ArticulationMark(
                    position=i,
                    articulation=ArticulationType.BREATH,
                ))

            if articulation:
                marks.append(ArticulationMark(
                    position=i,
                    articulation=articulation,
                ))

        return marks

    def generate_slurs(
        self,
        pitches: List[str],
        phrase_boundaries: List[int],
    ) -> List[SlurMark]:
        """
        Genera ligaduras de expresión (slurs).

        Los slurs agrupan notas que pertenecen al mismo gesto melódico.

        Args:
            pitches: Lista de pitches
            phrase_boundaries: Índices donde empiezan/terminan frases

        Returns:
            Lista de SlurMarks
        """
        from music21 import pitch as m21_pitch

        slurs = []
        current_slur_start = 0

        for i in range(1, len(pitches)):
            try:
                p1 = m21_pitch.Pitch(pitches[i-1])
                p2 = m21_pitch.Pitch(pitches[i])
                interval = abs(int(p2.midi - p1.midi))
            except Exception:
                interval = 0

            # Terminar slur si:
            # - Hay un salto grande (> quinta)
            # - Es límite de frase
            # - El slur es muy largo
            should_end_slur = (
                interval > 7 or
                i in phrase_boundaries or
                (i - current_slur_start) >= self.slur_length
            )

            if should_end_slur:
                # Solo crear slur si tiene al menos 2 notas
                if i - current_slur_start >= 2:
                    slurs.append(SlurMark(
                        start_position=current_slur_start,
                        end_position=i - 1,
                    ))
                current_slur_start = i

        # Slur final
        if len(pitches) - current_slur_start >= 2:
            slurs.append(SlurMark(
                start_position=current_slur_start,
                end_position=len(pitches) - 1,
            ))

        return slurs

    def generate_phrase_breaths(
        self,
        phrase_boundaries: List[int],
        total_notes: int,
    ) -> List[ArticulationMark]:
        """
        Genera marcas de respiración en límites de frase.

        Args:
            phrase_boundaries: Índices de límites de frase
            total_notes: Total de notas

        Returns:
            Lista de marcas de respiración
        """
        breaths = []

        for boundary in phrase_boundaries:
            if 0 < boundary < total_notes:
                breaths.append(ArticulationMark(
                    position=boundary - 1,  # Respiración antes del límite
                    articulation=ArticulationType.BREATH,
                ))

        return breaths

    @staticmethod
    def get_lilypond_articulation(articulation: ArticulationType) -> str:
        """Convierte articulación a comando LilyPond."""
        commands = {
            ArticulationType.STACCATO: "-.",
            ArticulationType.STACCATISSIMO: "-!",
            ArticulationType.TENUTO: "--",
            ArticulationType.ACCENT: "->",
            ArticulationType.MARCATO: "-^",
            ArticulationType.PORTATO: "-_",
            ArticulationType.FERMATA: "\\fermata",
            ArticulationType.BREATH: "\\breathe",
        }
        return commands.get(articulation, "")


def apply_articulations_to_staff(
    staff,  # abjad.Staff
    articulations: List[ArticulationMark],
    slurs: List[SlurMark],
) -> None:
    """
    Aplica articulaciones y slurs a un staff de Abjad.

    Args:
        staff: Staff de Abjad
        articulations: Lista de marcas de articulación
        slurs: Lista de slurs
    """
    import abjad

    leaves = list(abjad.select.leaves(staff))
    notes = [l for l in leaves if isinstance(l, abjad.Note)]

    # Aplicar articulaciones
    for mark in articulations:
        if mark.position >= len(notes):
            continue

        note = notes[mark.position]

        if mark.articulation == ArticulationType.STACCATO:
            abjad.attach(abjad.Articulation("staccato"), note)
        elif mark.articulation == ArticulationType.STACCATISSIMO:
            abjad.attach(abjad.Articulation("staccatissimo"), note)
        elif mark.articulation == ArticulationType.TENUTO:
            abjad.attach(abjad.Articulation("tenuto"), note)
        elif mark.articulation == ArticulationType.ACCENT:
            abjad.attach(abjad.Articulation("accent"), note)
        elif mark.articulation == ArticulationType.MARCATO:
            abjad.attach(abjad.Articulation("marcato"), note)
        elif mark.articulation == ArticulationType.FERMATA:
            abjad.attach(abjad.Fermata(), note)
        elif mark.articulation == ArticulationType.BREATH:
            # Breath mark después de la nota
            abjad.attach(abjad.LilyPondLiteral("\\breathe", site="after"), note)

    # Aplicar slurs
    for slur in slurs:
        if slur.start_position >= len(notes) or slur.end_position >= len(notes):
            continue

        start_note = notes[slur.start_position]
        end_note = notes[slur.end_position]

        abjad.attach(abjad.StartSlur(), start_note)
        abjad.attach(abjad.StopSlur(), end_note)
