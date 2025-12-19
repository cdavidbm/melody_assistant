"""
Dinámicas automáticas basadas en estructura musical.
Genera marcas dinámicas (p, f, cresc, dim) según contorno y forma.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class DynamicLevel(Enum):
    """Niveles dinámicos."""
    PPP = "ppp"
    PP = "pp"
    P = "p"
    MP = "mp"
    MF = "mf"
    F = "f"
    FF = "ff"
    FFF = "fff"

    @property
    def intensity(self) -> int:
        """Retorna intensidad numérica (1-8)."""
        levels = [
            DynamicLevel.PPP, DynamicLevel.PP, DynamicLevel.P, DynamicLevel.MP,
            DynamicLevel.MF, DynamicLevel.F, DynamicLevel.FF, DynamicLevel.FFF
        ]
        return levels.index(self) + 1


class DynamicChange(Enum):
    """Tipos de cambio dinámico."""
    CRESCENDO = "crescendo"
    DECRESCENDO = "decrescendo"
    DIMINUENDO = "diminuendo"
    SUBITO_PIANO = "subito_p"
    SUBITO_FORTE = "subito_f"
    SFORZANDO = "sfz"
    FORTEPIANO = "fp"


@dataclass
class DynamicMark:
    """Representa una marca dinámica en la partitura."""
    position: int           # Índice de la nota
    level: Optional[DynamicLevel] = None
    change: Optional[DynamicChange] = None
    duration_beats: float = 0  # Para crescendo/dim: duración en pulsos


@dataclass
class DynamicPlan:
    """Plan dinámico para una pieza completa."""
    marks: List[DynamicMark]
    base_level: DynamicLevel = DynamicLevel.MF
    climax_level: DynamicLevel = DynamicLevel.F
    cadence_level: DynamicLevel = DynamicLevel.P


class DynamicGenerator:
    """
    Genera dinámicas automáticas basadas en la estructura musical.

    Las dinámicas siguen principios de fraseo natural:
    - Crescendo hacia el clímax
    - Diminuendo después del clímax
    - Piano en cadencias
    - Contrastes entre frases
    """

    def __init__(
        self,
        base_level: DynamicLevel = DynamicLevel.MF,
        climax_level: DynamicLevel = DynamicLevel.F,
        style: str = "classical",
    ):
        """
        Inicializa el generador.

        Args:
            base_level: Nivel dinámico base
            climax_level: Nivel para clímax
            style: "baroque", "classical", "romantic"
        """
        self.base_level = base_level
        self.climax_level = climax_level
        self.style = style

        # Ajustar según estilo
        if style == "baroque":
            self.use_terraced_dynamics = True
            self.use_hairpins = False
        elif style == "romantic":
            self.use_terraced_dynamics = False
            self.use_hairpins = True
            self.climax_level = DynamicLevel.FF
        else:  # classical
            self.use_terraced_dynamics = False
            self.use_hairpins = True

    def generate_phrase_dynamics(
        self,
        phrase_length: int,
        climax_position: float = 0.7,
        is_antecedent: bool = True,
    ) -> List[DynamicMark]:
        """
        Genera dinámicas para una frase.

        Args:
            phrase_length: Número de notas en la frase
            climax_position: Posición del clímax (0.0-1.0)
            is_antecedent: Si es frase antecedente

        Returns:
            Lista de marcas dinámicas
        """
        marks = []

        # Índice del clímax
        climax_idx = int(phrase_length * climax_position)

        # Marca inicial
        if is_antecedent:
            marks.append(DynamicMark(
                position=0,
                level=self.base_level,
            ))
        else:
            # Consecuente puede empezar más suave o igual
            marks.append(DynamicMark(
                position=0,
                level=DynamicLevel.MP if is_antecedent else self.base_level,
            ))

        # Crescendo hacia clímax
        if self.use_hairpins and climax_idx > 2:
            crescendo_start = max(0, climax_idx - int(phrase_length * 0.3))
            marks.append(DynamicMark(
                position=crescendo_start,
                change=DynamicChange.CRESCENDO,
                duration_beats=climax_idx - crescendo_start,
            ))

        # Clímax
        marks.append(DynamicMark(
            position=climax_idx,
            level=self.climax_level,
        ))

        # Diminuendo después del clímax
        if self.use_hairpins and phrase_length - climax_idx > 2:
            marks.append(DynamicMark(
                position=climax_idx + 1,
                change=DynamicChange.DIMINUENDO,
                duration_beats=phrase_length - climax_idx - 2,
            ))

        # Cadencia (más suave)
        if phrase_length > 4:
            marks.append(DynamicMark(
                position=phrase_length - 2,
                level=DynamicLevel.P,
            ))

        return marks

    def generate_period_dynamics(
        self,
        num_measures: int,
        notes_per_measure: int = 4,
        climax_measure: int = None,
    ) -> DynamicPlan:
        """
        Genera plan dinámico para un período completo.

        Args:
            num_measures: Número de compases
            notes_per_measure: Notas por compás aproximadas
            climax_measure: Compás del clímax (None = automático)

        Returns:
            Plan dinámico completo
        """
        marks = []
        total_notes = num_measures * notes_per_measure
        midpoint = num_measures // 2

        if climax_measure is None:
            climax_measure = int(num_measures * 0.7)

        climax_note = climax_measure * notes_per_measure

        # Antecedente
        antecedent_marks = self.generate_phrase_dynamics(
            phrase_length=midpoint * notes_per_measure,
            climax_position=0.6,
            is_antecedent=True,
        )
        marks.extend(antecedent_marks)

        # Consecuente (offset por la longitud del antecedente)
        consequent_start = midpoint * notes_per_measure
        consequent_marks = self.generate_phrase_dynamics(
            phrase_length=(num_measures - midpoint) * notes_per_measure,
            climax_position=0.5,
            is_antecedent=False,
        )

        # Ajustar posiciones del consecuente
        for mark in consequent_marks:
            mark.position += consequent_start

        marks.extend(consequent_marks)

        # Clímax principal de la pieza
        marks.append(DynamicMark(
            position=climax_note,
            level=self.climax_level,
        ))

        # Final
        marks.append(DynamicMark(
            position=total_notes - 1,
            level=DynamicLevel.P,
        ))

        return DynamicPlan(
            marks=self._deduplicate_marks(marks),
            base_level=self.base_level,
            climax_level=self.climax_level,
            cadence_level=DynamicLevel.P,
        )

    def _deduplicate_marks(
        self,
        marks: List[DynamicMark],
    ) -> List[DynamicMark]:
        """Elimina marcas duplicadas en la misma posición."""
        seen_positions = {}

        for mark in marks:
            pos = mark.position
            if pos not in seen_positions:
                seen_positions[pos] = mark
            else:
                # Preferir niveles sobre cambios
                if mark.level and not seen_positions[pos].level:
                    seen_positions[pos] = mark

        # Ordenar por posición
        return sorted(seen_positions.values(), key=lambda m: m.position)

    def get_dynamic_at_position(
        self,
        plan: DynamicPlan,
        position: int,
    ) -> Optional[DynamicLevel]:
        """
        Obtiene el nivel dinámico en una posición específica.

        Interpola entre marcas si es necesario.
        """
        # Buscar marca exacta
        for mark in plan.marks:
            if mark.position == position and mark.level:
                return mark.level

        # Interpolar entre marcas
        prev_mark = None
        next_mark = None

        for mark in plan.marks:
            if mark.position < position and mark.level:
                prev_mark = mark
            elif mark.position > position and mark.level:
                next_mark = mark
                break

        if prev_mark:
            return prev_mark.level
        return plan.base_level

    @staticmethod
    def get_lilypond_dynamic(level: DynamicLevel) -> str:
        """Convierte nivel dinámico a comando LilyPond."""
        return f"\\{level.value}"

    @staticmethod
    def get_lilypond_hairpin(change: DynamicChange) -> str:
        """Convierte cambio dinámico a comando LilyPond."""
        hairpins = {
            DynamicChange.CRESCENDO: "\\<",
            DynamicChange.DECRESCENDO: "\\>",
            DynamicChange.DIMINUENDO: "\\>",
            DynamicChange.SFORZANDO: "\\sfz",
            DynamicChange.FORTEPIANO: "\\fp",
            DynamicChange.SUBITO_PIANO: "\\p",
            DynamicChange.SUBITO_FORTE: "\\f",
        }
        return hairpins.get(change, "")


def apply_dynamics_to_staff(
    staff,  # abjad.Staff
    plan: DynamicPlan,
) -> None:
    """
    Aplica un plan dinámico a un staff de Abjad.

    Args:
        staff: Staff de Abjad
        plan: Plan dinámico a aplicar
    """
    import abjad

    leaves = list(abjad.select.leaves(staff))

    for mark in plan.marks:
        if mark.position >= len(leaves):
            continue

        leaf = leaves[mark.position]

        # Aplicar nivel dinámico
        if mark.level:
            # Manejar tanto enums como strings
            level_str = mark.level.value if hasattr(mark.level, 'value') else str(mark.level)
            dynamic = abjad.Dynamic(level_str)
            abjad.attach(dynamic, leaf)

        # Aplicar cambio (hairpin)
        if mark.change:
            if mark.change in [DynamicChange.CRESCENDO]:
                hairpin = abjad.StartHairpin("<")
                abjad.attach(hairpin, leaf)
            elif mark.change in [DynamicChange.DECRESCENDO, DynamicChange.DIMINUENDO]:
                hairpin = abjad.StartHairpin(">")
                abjad.attach(hairpin, leaf)

            # Terminar hairpin después de la duración especificada
            if mark.duration_beats > 0:
                end_pos = min(
                    mark.position + int(mark.duration_beats),
                    len(leaves) - 1
                )
                end_leaf = leaves[end_pos]
                abjad.attach(abjad.StopHairpin(), end_leaf)
