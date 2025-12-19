"""
Sistema de memoria para decisiones de generación melódica.

Registra todas las decisiones tomadas durante la generación,
permitiendo correcciones quirúrgicas sin regenerar desde cero.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class DecisionType(Enum):
    """Tipos de decisiones registradas."""
    PITCH = "pitch"
    RHYTHM = "rhythm"
    ORNAMENT = "ornament"
    DYNAMIC = "dynamic"
    ARTICULATION = "articulation"


@dataclass
class ScoreBreakdown:
    """Desglose detallado de puntuaciones por criterio."""
    voice_leading: float = 0.0
    harmonic: float = 0.0
    contour: float = 0.0
    tendency: float = 0.0
    markov: float = 0.0
    variety: float = 0.0
    range: float = 0.0

    def total(self) -> float:
        """Calcula puntuación total ponderada."""
        weights = {
            'voice_leading': 0.28,
            'harmonic': 0.22,
            'contour': 0.15,
            'tendency': 0.12,
            'markov': 0.10,
            'variety': 0.08,
            'range': 0.05,
        }
        total = 0.0
        for criterion, weight in weights.items():
            total += getattr(self, criterion) * weight
        return total

    def to_dict(self) -> Dict[str, float]:
        """Convierte a diccionario."""
        return {
            'voice_leading': self.voice_leading,
            'harmonic': self.harmonic,
            'contour': self.contour,
            'tendency': self.tendency,
            'markov': self.markov,
            'variety': self.variety,
            'range': self.range,
            'total': self.total(),
        }


@dataclass
class Alternative:
    """Una alternativa considerada durante la decisión."""
    value: Any  # pitch, duration, etc.
    score: float
    score_breakdown: Optional[ScoreBreakdown] = None
    reason_rejected: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        result = {
            'value': str(self.value),
            'score': self.score,
        }
        if self.score_breakdown:
            result['breakdown'] = self.score_breakdown.to_dict()
        if self.reason_rejected:
            result['reason_rejected'] = self.reason_rejected
        return result


@dataclass
class HarmonicContext:
    """Contexto armónico en el momento de la decisión."""
    chord_degree: int  # I, ii, V, etc. como número
    chord_tones: List[int]  # Grados de la escala que son notas del acorde
    function: str  # "tonic", "dominant", "subdominant", etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'chord_degree': self.chord_degree,
            'chord_tones': self.chord_tones,
            'function': self.function,
        }


@dataclass
class MelodicContext:
    """Contexto melódico en el momento de la decisión."""
    previous_pitch: Optional[str]
    previous_interval: Optional[int]  # En semitonos
    direction: int  # 1 = ascendente, 0 = estático, -1 = descendente
    phrase_position: float  # 0.0 a 1.0, posición dentro de la frase
    is_climax: bool
    contour_target: Optional[int]  # Grado objetivo según contorno planeado

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'previous_pitch': self.previous_pitch,
            'previous_interval': self.previous_interval,
            'direction': self.direction,
            'phrase_position': self.phrase_position,
            'is_climax': self.is_climax,
            'contour_target': self.contour_target,
        }


@dataclass
class MetricContext:
    """Contexto métrico en el momento de la decisión."""
    measure: int
    beat: float  # 1.0, 1.5, 2.0, etc.
    beat_strength: str  # "strong", "weak"
    subdivision: int  # 1, 2, 4, 8 (nivel de subdivisión)
    is_downbeat: bool
    is_phrase_start: bool
    is_phrase_end: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            'measure': self.measure,
            'beat': self.beat,
            'beat_strength': self.beat_strength,
            'subdivision': self.subdivision,
            'is_downbeat': self.is_downbeat,
            'is_phrase_start': self.is_phrase_start,
            'is_phrase_end': self.is_phrase_end,
        }


@dataclass
class Decision:
    """
    Una decisión individual tomada durante la generación.

    Almacena qué se eligió, qué alternativas había,
    y todo el contexto que llevó a esa decisión.
    """
    # Identificación
    decision_type: DecisionType
    measure: int
    beat: float
    index: int  # Índice global de la nota/evento

    # Decisión tomada
    chosen_value: Any
    chosen_score: float
    score_breakdown: ScoreBreakdown

    # Alternativas consideradas
    alternatives: List[Alternative] = field(default_factory=list)

    # Contexto completo
    harmonic_context: Optional[HarmonicContext] = None
    melodic_context: Optional[MelodicContext] = None
    metric_context: Optional[MetricContext] = None

    # Historial de correcciones
    fix_attempts: List[Dict[str, Any]] = field(default_factory=list)
    is_fixed: bool = False

    def get_valid_alternatives(self, exclude_values: Optional[List[Any]] = None) -> List[Alternative]:
        """
        Obtiene alternativas válidas, excluyendo valores específicos.

        Args:
            exclude_values: Valores a excluir (ya intentados, etc.)

        Returns:
            Lista de alternativas ordenadas por score
        """
        exclude = set(str(v) for v in (exclude_values or []))
        exclude.add(str(self.chosen_value))

        valid = [
            alt for alt in self.alternatives
            if str(alt.value) not in exclude
        ]

        return sorted(valid, key=lambda a: a.score, reverse=True)

    def record_fix_attempt(self, new_value: Any, reason: str, success: bool):
        """
        Registra un intento de corrección.

        Args:
            new_value: Nuevo valor intentado
            reason: Razón del cambio
            success: Si la corrección fue exitosa
        """
        self.fix_attempts.append({
            'previous_value': str(self.chosen_value),
            'new_value': str(new_value),
            'reason': reason,
            'success': success,
            'attempt_number': len(self.fix_attempts) + 1,
        })

        if success:
            self.chosen_value = new_value
            self.is_fixed = True

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización/debug."""
        return {
            'type': self.decision_type.value,
            'location': {
                'measure': self.measure,
                'beat': self.beat,
                'index': self.index,
            },
            'chosen': {
                'value': str(self.chosen_value),
                'score': self.chosen_score,
                'breakdown': self.score_breakdown.to_dict(),
            },
            'alternatives': [alt.to_dict() for alt in self.alternatives],
            'context': {
                'harmonic': self.harmonic_context.to_dict() if self.harmonic_context else None,
                'melodic': self.melodic_context.to_dict() if self.melodic_context else None,
                'metric': self.metric_context.to_dict() if self.metric_context else None,
            },
            'fix_attempts': self.fix_attempts,
            'is_fixed': self.is_fixed,
        }


class DecisionMemory:
    """
    Memoria completa de todas las decisiones de una generación.

    Permite:
    - Registrar decisiones durante la generación
    - Buscar decisiones por ubicación (compás, beat)
    - Obtener alternativas para correcciones
    - Rastrear intentos de corrección
    """

    def __init__(self):
        """Inicializa la memoria vacía."""
        self._decisions: List[Decision] = []
        self._by_location: Dict[Tuple[int, float], Decision] = {}
        self._by_index: Dict[int, Decision] = {}
        self._correction_history: List[Dict[str, Any]] = []
        self._generation_metadata: Dict[str, Any] = {}

    def set_metadata(self, **kwargs):
        """
        Guarda metadatos de la generación.

        Args:
            **kwargs: key_name, mode, meter, num_measures, etc.
        """
        self._generation_metadata.update(kwargs)

    def record_decision(self, decision: Decision):
        """
        Registra una nueva decisión.

        Args:
            decision: La decisión a registrar
        """
        self._decisions.append(decision)
        self._by_location[(decision.measure, decision.beat)] = decision
        self._by_index[decision.index] = decision

    def get_by_location(self, measure: int, beat: float) -> Optional[Decision]:
        """
        Busca una decisión por ubicación.

        Args:
            measure: Número de compás (1-indexed)
            beat: Beat dentro del compás (1.0, 1.5, 2.0, etc.)

        Returns:
            Decision si existe, None si no
        """
        return self._by_location.get((measure, beat))

    def get_by_index(self, index: int) -> Optional[Decision]:
        """
        Busca una decisión por índice global.

        Args:
            index: Índice de la nota (0-indexed)

        Returns:
            Decision si existe, None si no
        """
        return self._by_index.get(index)

    def get_decisions_in_measure(self, measure: int) -> List[Decision]:
        """
        Obtiene todas las decisiones en un compás.

        Args:
            measure: Número de compás

        Returns:
            Lista de decisiones en ese compás
        """
        return [d for d in self._decisions if d.measure == measure]

    def get_nearby_decisions(self, measure: int, beat: float, radius: int = 2) -> List[Decision]:
        """
        Obtiene decisiones cercanas a una ubicación.

        Útil para considerar contexto al hacer correcciones.

        Args:
            measure: Compás central
            beat: Beat central
            radius: Número de notas antes/después

        Returns:
            Lista de decisiones cercanas
        """
        target = self.get_by_location(measure, beat)
        if not target:
            return []

        target_idx = target.index
        return [
            d for d in self._decisions
            if abs(d.index - target_idx) <= radius
        ]

    def record_correction_round(
        self,
        round_number: int,
        issues_found: List[Dict[str, Any]],
        issues_fixed: List[Dict[str, Any]],
        score_before: float,
        score_after: float,
    ):
        """
        Registra una ronda de corrección.

        Args:
            round_number: Número de ronda (1-5)
            issues_found: Problemas encontrados
            issues_fixed: Problemas corregidos
            score_before: Score antes de corrección
            score_after: Score después de corrección
        """
        self._correction_history.append({
            'round': round_number,
            'issues_found': issues_found,
            'issues_fixed': issues_fixed,
            'score_before': score_before,
            'score_after': score_after,
            'improvement': score_after - score_before,
        })

    def get_unfixed_decisions(self) -> List[Decision]:
        """Obtiene decisiones que no han sido corregidas."""
        return [d for d in self._decisions if not d.is_fixed]

    def get_fixed_decisions(self) -> List[Decision]:
        """Obtiene decisiones que han sido corregidas."""
        return [d for d in self._decisions if d.is_fixed]

    def get_failed_attempts(self) -> List[Tuple[Decision, Dict[str, Any]]]:
        """Obtiene intentos de corrección fallidos."""
        result = []
        for decision in self._decisions:
            for attempt in decision.fix_attempts:
                if not attempt['success']:
                    result.append((decision, attempt))
        return result

    def should_continue_correcting(
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
            target_score: Score objetivo (default 80%)
            max_rounds: Máximo de rondas (default 5)
            min_improvement: Mejora mínima para continuar (default 2%)

        Returns:
            Tupla (continuar: bool, razón: str)
        """
        rounds = len(self._correction_history)

        # Alcanzamos el objetivo
        if current_score >= target_score:
            return False, f"score_achieved ({current_score:.1%} >= {target_score:.1%})"

        # Máximo de rondas
        if rounds >= max_rounds:
            return False, f"max_rounds_reached ({rounds}/{max_rounds})"

        # Rendimientos decrecientes
        if rounds >= 2:
            last_improvement = self._correction_history[-1]['improvement']
            if last_improvement < min_improvement:
                return False, f"diminishing_returns (mejora {last_improvement:.1%} < {min_improvement:.1%})"

        return True, "continue"

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la memoria."""
        total = len(self._decisions)
        fixed = len(self.get_fixed_decisions())

        return {
            'total_decisions': total,
            'fixed_decisions': fixed,
            'fix_rate': fixed / total if total > 0 else 0,
            'correction_rounds': len(self._correction_history),
            'total_fix_attempts': sum(
                len(d.fix_attempts) for d in self._decisions
            ),
            'metadata': self._generation_metadata,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializa toda la memoria a diccionario."""
        return {
            'metadata': self._generation_metadata,
            'decisions': [d.to_dict() for d in self._decisions],
            'correction_history': self._correction_history,
            'statistics': self.get_statistics(),
        }

    def clear(self):
        """Limpia toda la memoria para nueva generación."""
        self._decisions.clear()
        self._by_location.clear()
        self._by_index.clear()
        self._correction_history.clear()
        self._generation_metadata.clear()

    def __len__(self) -> int:
        """Número de decisiones registradas."""
        return len(self._decisions)

    def __iter__(self):
        """Itera sobre las decisiones."""
        return iter(self._decisions)
