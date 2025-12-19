"""
Corrector quirúrgico para melodías generadas.

Corrige problemas específicos sin regenerar toda la melodía,
usando la memoria de decisiones para elegir alternativas válidas.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

import abjad
from music21 import pitch as m21_pitch

logger = logging.getLogger(__name__)

from .memory import DecisionMemory, Decision, Alternative
from .validation import ValidationIssue, IssueType, IssueSeverity, ValidationReport


@dataclass
class CorrectionResult:
    """Resultado de un intento de corrección."""
    success: bool
    issue: ValidationIssue
    original_value: str
    new_value: Optional[str] = None
    reason: str = ""
    alternatives_tried: List[str] = field(default_factory=list)


@dataclass
class CorrectionRound:
    """Resultado de una ronda completa de correcciones."""
    round_number: int
    issues_attempted: int
    issues_fixed: int
    score_before: float
    score_after: float
    corrections: List[CorrectionResult] = field(default_factory=list)

    @property
    def improvement(self) -> float:
        """Mejora en el score."""
        return self.score_after - self.score_before

    @property
    def fix_rate(self) -> float:
        """Tasa de éxito de correcciones."""
        if self.issues_attempted == 0:
            return 0.0
        return self.issues_fixed / self.issues_attempted


class SurgicalCorrector:
    """
    Corrector quirúrgico que modifica notas específicas sin regenerar.

    Usa la memoria de decisiones para:
    1. Encontrar la decisión original de cada nota problemática
    2. Seleccionar una alternativa válida que resuelva el problema
    3. Aplicar el cambio directamente al staff
    """

    def __init__(
        self,
        staff: abjad.Staff,
        memory: DecisionMemory,
        key_name: str,
        mode: str,
        max_attempts_per_issue: int = 3,
    ):
        """
        Inicializa el corrector quirúrgico.

        Args:
            staff: Staff de Abjad a corregir
            memory: Memoria de decisiones de la generación
            key_name: Tonalidad de la pieza
            mode: Modo musical
            max_attempts_per_issue: Máximo de intentos por issue
        """
        self.staff = staff
        self.memory = memory
        self.key_name = key_name
        self.mode = mode
        self.max_attempts_per_issue = max_attempts_per_issue

        # Historial de correcciones
        self._correction_history: List[CorrectionRound] = []
        self._failed_corrections: Dict[Tuple[int, float], List[str]] = {}

    def fix_issues(
        self,
        issues: List[ValidationIssue],
        score_before: float,
    ) -> CorrectionRound:
        """
        Intenta corregir una lista de issues.

        Args:
            issues: Lista de problemas a corregir
            score_before: Score antes de las correcciones

        Returns:
            CorrectionRound con resultados
        """
        round_number = len(self._correction_history) + 1
        corrections = []
        issues_fixed = 0

        # Ordenar issues por severidad (críticos primero)
        sorted_issues = sorted(
            issues,
            key=lambda i: (
                0 if i.severity == IssueSeverity.CRITICAL else
                1 if i.severity == IssueSeverity.WARNING else 2
            )
        )

        for issue in sorted_issues:
            result = self._fix_single_issue(issue)
            corrections.append(result)
            if result.success:
                issues_fixed += 1

        # Crear registro de la ronda
        correction_round = CorrectionRound(
            round_number=round_number,
            issues_attempted=len(issues),
            issues_fixed=issues_fixed,
            score_before=score_before,
            score_after=0.0,  # Se actualizará después de revalidar
            corrections=corrections,
        )

        self._correction_history.append(correction_round)

        # Registrar en memoria
        self.memory.record_correction_round(
            round_number=round_number,
            issues_found=[i.to_dict() for i in issues],
            issues_fixed=[c.issue.to_dict() for c in corrections if c.success],
            score_before=score_before,
            score_after=0.0,
        )

        return correction_round

    def _fix_single_issue(self, issue: ValidationIssue) -> CorrectionResult:
        """
        Intenta corregir un issue individual.

        Args:
            issue: El problema a corregir

        Returns:
            CorrectionResult con el resultado
        """
        location_key = (issue.measure, issue.beat)

        # Buscar la decisión original en la memoria
        # Primero por ubicación exacta
        decision = self.memory.get_by_location(issue.measure, issue.beat)

        # Si no se encuentra, intentar por índice de nota
        if decision is None and issue.note_index is not None:
            decision = self.memory.get_by_index(issue.note_index)

        # Si aún no se encuentra, buscar con tolerancia de beat
        if decision is None:
            # Buscar decisiones en el mismo compás con beat cercano
            beat_tolerance = 0.3
            for dec in self.memory._decisions:
                if (dec.metric_context.measure == issue.measure and
                    abs(dec.metric_context.beat - issue.beat) < beat_tolerance):
                    decision = dec
                    break

        if decision is None:
            return CorrectionResult(
                success=False,
                issue=issue,
                original_value=issue.actual_value or "unknown",
                reason="No se encontró decisión en memoria para esta ubicación",
            )

        # Obtener alternativas que no hemos intentado
        already_tried = self._failed_corrections.get(location_key, [])
        already_tried.append(str(decision.chosen_value))

        valid_alternatives = decision.get_valid_alternatives(
            exclude_values=already_tried
        )

        if not valid_alternatives:
            return CorrectionResult(
                success=False,
                issue=issue,
                original_value=str(decision.chosen_value),
                reason="No hay alternativas válidas disponibles",
                alternatives_tried=already_tried,
            )

        # Intentar alternativas en orden de score
        for alt in valid_alternatives[:self.max_attempts_per_issue]:
            if self._is_valid_alternative(alt, issue):
                # Aplicar la corrección al staff
                success = self._apply_correction(decision, alt.value, issue)

                if success:
                    # Registrar en la decisión
                    decision.record_fix_attempt(
                        new_value=alt.value,
                        reason=f"Corrección de {issue.issue_type.value}",
                        success=True,
                    )

                    return CorrectionResult(
                        success=True,
                        issue=issue,
                        original_value=str(decision.chosen_value),
                        new_value=str(alt.value),
                        reason=f"Reemplazado con alternativa (score: {alt.score:.2f})",
                        alternatives_tried=already_tried + [str(alt.value)],
                    )

            # Registrar intento fallido
            already_tried.append(str(alt.value))

        # No se encontró alternativa válida
        self._failed_corrections[location_key] = already_tried

        return CorrectionResult(
            success=False,
            issue=issue,
            original_value=str(decision.chosen_value),
            reason="Ninguna alternativa resuelve el problema",
            alternatives_tried=already_tried,
        )

    def _is_valid_alternative(
        self,
        alternative: Alternative,
        issue: ValidationIssue,
    ) -> bool:
        """
        Verifica si una alternativa resuelve el issue.

        Args:
            alternative: La alternativa a evaluar
            issue: El problema a resolver

        Returns:
            True si la alternativa es válida
        """
        alt_value = str(alternative.value)

        if issue.issue_type == IssueType.OUT_OF_KEY:
            # Verificar que la alternativa está en la escala
            try:
                from music21 import key
                expected_key = key.Key(self.key_name, self.mode)
                scale_pitch_classes = {p.pitchClass for p in expected_key.getPitches()}

                alt_pitch = m21_pitch.Pitch(alt_value)
                return alt_pitch.pitchClass in scale_pitch_classes
            except Exception as e:
                logger.debug(f"Error verificando alternativa {alt_value} para OUT_OF_KEY: {e}")
                return False

        elif issue.issue_type == IssueType.LARGE_LEAP:
            # Para saltos, necesitamos verificar con el contexto
            # Por ahora, cualquier alternativa con mejor score es válida
            return alternative.score > 0.5

        elif issue.issue_type == IssueType.RANGE_EXCEEDED:
            # Verificar que la alternativa está en rango
            try:
                alt_pitch = m21_pitch.Pitch(alt_value)
                # Rango típico: C3 a C6
                return 48 <= alt_pitch.midi <= 84
            except Exception as e:
                logger.debug(f"Error verificando rango de {alt_value}: {e}")
                return False

        # Para otros tipos, aceptar cualquier alternativa con score razonable
        return alternative.score > 0.3

    def _apply_correction(
        self,
        decision: Decision,
        new_value: Any,
        issue: ValidationIssue,
    ) -> bool:
        """
        Aplica la corrección al staff de Abjad.

        Args:
            decision: La decisión original
            new_value: El nuevo valor a aplicar
            issue: El issue que se está corrigiendo

        Returns:
            True si se aplicó correctamente
        """
        try:
            # Encontrar la nota en el staff por índice
            leaves = list(abjad.select.leaves(self.staff))
            note_index = decision.index

            if note_index >= len(leaves):
                return False

            leaf = leaves[note_index]

            if not isinstance(leaf, abjad.Note):
                return False

            # Crear nuevo pitch
            new_pitch_str = str(new_value)

            # Convertir de music21 a LilyPond si es necesario
            from .converters import AbjadMusic21Converter
            lily_pitch = AbjadMusic21Converter.music21_pitch_to_lilypond(new_pitch_str)

            # Mantener la duración original
            original_duration = leaf.written_duration

            # Crear nueva nota
            new_note = abjad.Note(f"{lily_pitch}{original_duration}")

            # Copiar indicadores adjuntos
            indicators = abjad.get.indicators(leaf)
            for indicator in indicators:
                try:
                    abjad.attach(indicator, new_note)
                except Exception as e:
                    logger.debug(f"No se pudo copiar indicador {indicator}: {e}")

            # Reemplazar en el contenedor padre
            parent = abjad.get.parentage(leaf).parent
            if parent is not None:
                index_in_parent = list(parent).index(leaf)
                parent[index_in_parent] = new_note

            return True

        except Exception as e:
            logger.warning(f"Error aplicando corrección: {e}")
            return False

    def get_correction_history(self) -> List[CorrectionRound]:
        """Obtiene el historial de correcciones."""
        return self._correction_history

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las correcciones."""
        total_attempted = sum(r.issues_attempted for r in self._correction_history)
        total_fixed = sum(r.issues_fixed for r in self._correction_history)

        return {
            'total_rounds': len(self._correction_history),
            'total_issues_attempted': total_attempted,
            'total_issues_fixed': total_fixed,
            'overall_fix_rate': total_fixed / total_attempted if total_attempted > 0 else 0.0,
            'rounds': [
                {
                    'round': r.round_number,
                    'attempted': r.issues_attempted,
                    'fixed': r.issues_fixed,
                    'improvement': r.improvement,
                }
                for r in self._correction_history
            ],
        }

    def should_continue(
        self,
        current_score: float,
        target_score: float = 0.80,
        max_rounds: int = 5,
        min_improvement: float = 0.02,
    ) -> Tuple[bool, str]:
        """
        Determina si se debe continuar corrigiendo.

        Args:
            current_score: Score actual
            target_score: Score objetivo
            max_rounds: Máximo de rondas
            min_improvement: Mejora mínima requerida

        Returns:
            Tupla (continuar, razón)
        """
        # Delegar a la memoria
        return self.memory.should_continue_correcting(
            current_score=current_score,
            target_score=target_score,
            max_rounds=max_rounds,
            min_improvement=min_improvement,
        )

    def update_round_score(self, round_index: int, score_after: float):
        """Actualiza el score final de una ronda."""
        if 0 <= round_index < len(self._correction_history):
            self._correction_history[round_index].score_after = score_after

            # Actualizar también en la memoria
            if round_index < len(self.memory._correction_history):
                self.memory._correction_history[round_index]['score_after'] = score_after
                self.memory._correction_history[round_index]['improvement'] = (
                    score_after - self._correction_history[round_index].score_before
                )
