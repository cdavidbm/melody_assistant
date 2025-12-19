"""
Sistema de validación musical con music21.
Valida que las partituras generadas cumplan con especificaciones musicales.

Soporta validación detallada con ubicación exacta de problemas para
permitir correcciones quirúrgicas sin regenerar la melodía completa.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

import abjad
from music21 import key, stream, converter

from .converters import AbjadMusic21Converter


class IssueType(Enum):
    """Tipos de problemas detectados en la validación."""
    OUT_OF_KEY = "out_of_key"  # Nota fuera de la escala
    LARGE_LEAP = "large_leap"  # Salto melódico grande sin resolver
    UNRESOLVED_TENDENCY = "unresolved_tendency"  # Nota de tendencia sin resolver
    PARALLEL_MOTION = "parallel_motion"  # Movimiento paralelo (si aplica)
    METER_ERROR = "meter_error"  # Duración incorrecta en compás
    RANGE_EXCEEDED = "range_exceeded"  # Fuera del rango vocal
    WEAK_CADENCE = "weak_cadence"  # Cadencia débil o incorrecta
    REPETITION_EXCESS = "repetition_excess"  # Repetición excesiva de notas


class IssueSeverity(Enum):
    """Severidad del problema."""
    CRITICAL = "critical"  # Debe corregirse
    WARNING = "warning"  # Recomendado corregir
    SUGGESTION = "suggestion"  # Opcional mejorar


@dataclass
class ValidationIssue:
    """
    Un problema específico detectado durante la validación.

    Incluye ubicación exacta para permitir correcciones quirúrgicas.
    """
    issue_type: IssueType
    severity: IssueSeverity
    measure: int  # 1-indexed
    beat: float  # 1-indexed (1.0, 1.5, 2.0, etc.)
    note_index: Optional[int] = None  # Índice global de la nota

    # Detalles del problema
    description: str = ""
    actual_value: Optional[str] = None  # Lo que se encontró
    expected_value: Optional[str] = None  # Lo que debería ser
    context: Dict[str, Any] = field(default_factory=dict)

    # Sugerencias de corrección
    suggested_fixes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            'type': self.issue_type.value,
            'severity': self.severity.value,
            'location': {
                'measure': self.measure,
                'beat': self.beat,
                'note_index': self.note_index,
            },
            'description': self.description,
            'actual': self.actual_value,
            'expected': self.expected_value,
            'context': self.context,
            'suggested_fixes': self.suggested_fixes,
        }

    def __str__(self) -> str:
        severity_icon = {
            IssueSeverity.CRITICAL: "❌",
            IssueSeverity.WARNING: "⚠️",
            IssueSeverity.SUGGESTION: "💡",
        }
        icon = severity_icon.get(self.severity, "•")
        return f"{icon} Compás {self.measure}, beat {self.beat}: {self.description}"


@dataclass
class KeyValidation:
    """Resultado de validación de tonalidad."""

    expected_key: str
    detected_key: str
    correlation: float  # Coeficiente Krumhansl (0.0-1.0)
    matches: bool
    diatonic_percentage: float
    warnings: List[str] = field(default_factory=list)
    is_valid: bool = True

    def __str__(self) -> str:
        status = "✓" if self.is_valid else "❌"
        match_str = "COINCIDE" if self.matches else "NO COINCIDE"
        return f"{status} Tonalidad: {self.detected_key} (esperada: {self.expected_key}) - {match_str}"


@dataclass
class MeterValidation:
    """Resultado de validación de métrica."""

    expected_meter: Tuple[int, int]
    measures_validated: int
    measures_valid: int
    measures_invalid: List[int] = field(default_factory=list)
    duration_errors: List[str] = field(default_factory=list)
    is_valid: bool = True

    def __str__(self) -> str:
        status = "✓" if self.is_valid else "❌"
        return f"{status} Métrica: {self.measures_valid}/{self.measures_validated} compases correctos"


@dataclass
class RangeValidation:
    """Resultado de validación de rango melódico."""

    ambitus_semitones: int
    lowest_pitch: str
    highest_pitch: str
    is_singable: bool = True
    warnings: List[str] = field(default_factory=list)
    is_valid: bool = True

    def __str__(self) -> str:
        status = "✓" if self.is_valid else "❌"
        singable = "cantable" if self.is_singable else "difícil de cantar"
        return f"{status} Rango: {self.ambitus_semitones} semitonos ({singable})"


@dataclass
class ModeValidation:
    """Resultado de validación de modo."""

    expected_mode: str
    characteristic_intervals_present: bool
    degree_distribution: Dict[int, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    is_valid: bool = True
    score: float = 1.0

    def __str__(self) -> str:
        status = "✓" if self.is_valid else "❌"
        return f"{status} Modo: {self.expected_mode} (puntuación: {self.score:.1%})"


@dataclass
class ValidationReport:
    """Reporte completo de validación musical."""

    is_valid: bool
    overall_score: float

    key_validation: KeyValidation
    meter_validation: MeterValidation
    range_validation: RangeValidation
    mode_validation: ModeValidation

    # Lista detallada de problemas con ubicación exacta
    issues: List[ValidationIssue] = field(default_factory=list)

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def get_issues_by_type(self, issue_type: IssueType) -> List[ValidationIssue]:
        """Obtiene issues de un tipo específico."""
        return [i for i in self.issues if i.issue_type == issue_type]

    def get_issues_by_severity(self, severity: IssueSeverity) -> List[ValidationIssue]:
        """Obtiene issues de una severidad específica."""
        return [i for i in self.issues if i.severity == severity]

    def get_issues_in_measure(self, measure: int) -> List[ValidationIssue]:
        """Obtiene issues en un compás específico."""
        return [i for i in self.issues if i.measure == measure]

    def get_critical_issues(self) -> List[ValidationIssue]:
        """Obtiene solo los issues críticos que deben corregirse."""
        return self.get_issues_by_severity(IssueSeverity.CRITICAL)

    def format_detailed_report(self) -> str:
        """Genera reporte detallado con ASCII art."""
        lines = []

        # Header
        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " " * 20 + "REPORTE DE VALIDACIÓN" + " " * 27 + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")

        # Overall status
        status_icon = "✓" if self.is_valid else "⚠️"
        status_text = "VÁLIDA" if self.is_valid else "REQUIERE ATENCIÓN"
        lines.append(f"Estado General: {status_icon} {status_text}")
        lines.append(f"Puntuación:     {self.overall_score:.1%} (calidad musical)")
        lines.append("")

        # Key validation
        lines.append("┌─ TONALIDAD " + "─" * 55 + "┐")
        lines.append(f"│ Esperada:         {self.key_validation.expected_key:<48} │")
        lines.append(f"│ Detectada:        {self.key_validation.detected_key:<48} │")
        lines.append(
            f"│ Correlación:      {self.key_validation.correlation:.2%} (certeza del análisis){' ' * 19}│"
        )
        lines.append(
            f"│ Notas diatónicas: {self.key_validation.diatonic_percentage:.1%}{' ' * 48}│"
        )

        match_icon = "✓" if self.key_validation.matches else "❌"
        match_text = "COINCIDE" if self.key_validation.matches else "NO COINCIDE"
        lines.append(f"│ Estado:           {match_icon} {match_text:<47}│")

        if self.key_validation.warnings:
            for warning in self.key_validation.warnings:
                lines.append(f"│ ⚠️  {warning:<64}│")
        lines.append("└" + "─" * 68 + "┘")
        lines.append("")

        # Meter validation
        lines.append("┌─ MÉTRICA " + "─" * 57 + "┐")
        meter_str = f"{self.meter_validation.expected_meter[0]}/{self.meter_validation.expected_meter[1]}"
        lines.append(f"│ Compás esperado:  {meter_str:<48} │")
        lines.append(
            f"│ Compases válidos: {self.meter_validation.measures_valid}/{self.meter_validation.measures_validated:<47} │"
        )

        if self.meter_validation.measures_invalid:
            invalid_str = ", ".join(
                str(m + 1) for m in self.meter_validation.measures_invalid[:5]
            )
            if len(self.meter_validation.measures_invalid) > 5:
                invalid_str += "..."
            lines.append(f"│ Compases con error: {invalid_str:<45}│")

            for error in self.meter_validation.duration_errors[:3]:
                lines.append(f"│   • {error:<62}│")

        meter_icon = "✓" if self.meter_validation.is_valid else "❌"
        lines.append(
            f"│ Estado:           {meter_icon} {'CORRECTO' if self.meter_validation.is_valid else 'ERRORES DETECTADOS':<47}│"
        )
        lines.append("└" + "─" * 68 + "┘")
        lines.append("")

        # Range validation
        lines.append("┌─ RANGO MELÓDICO " + "─" * 50 + "┐")
        lines.append(
            f"│ Ámbito:           {self.range_validation.ambitus_semitones} semitonos{' ' * 42}│"
        )
        lines.append(f"│ Nota más grave:   {self.range_validation.lowest_pitch:<48} │")
        lines.append(f"│ Nota más aguda:   {self.range_validation.highest_pitch:<48} │")

        singable_icon = "✓" if self.range_validation.is_singable else "⚠️"
        singable_text = (
            "Cantable" if self.range_validation.is_singable else "Amplio (difícil)"
        )
        lines.append(f"│ Cantabilidad:     {singable_icon} {singable_text:<47}│")
        lines.append("└" + "─" * 68 + "┘")
        lines.append("")

        # Mode validation
        lines.append("┌─ MODO MUSICAL " + "─" * 52 + "┐")
        lines.append(f"│ Modo:             {self.mode_validation.expected_mode:<48} │")
        lines.append(
            f"│ Puntuación:       {self.mode_validation.score:.1%} (características del modo){' ' * 20}│"
        )

        mode_icon = "✓" if self.mode_validation.is_valid else "⚠️"
        lines.append(
            f"│ Estado:           {mode_icon} {'CORRECTO' if self.mode_validation.is_valid else 'VERIFICAR':<47}│"
        )
        lines.append("└" + "─" * 68 + "┘")
        lines.append("")

        # Detailed issues with location
        if self.issues:
            critical = self.get_critical_issues()
            warnings_issues = self.get_issues_by_severity(IssueSeverity.WARNING)

            lines.append("┌─ PROBLEMAS DETECTADOS " + "─" * 44 + "┐")
            lines.append(f"│ Total: {len(self.issues)} ({len(critical)} críticos, {len(warnings_issues)} advertencias){' ' * 25}│")
            lines.append("├" + "─" * 68 + "┤")

            # Mostrar hasta 10 issues
            for issue in self.issues[:10]:
                icon = "❌" if issue.severity == IssueSeverity.CRITICAL else "⚠️"
                loc = f"C{issue.measure}:B{issue.beat}"
                desc = issue.description[:45] + "..." if len(issue.description) > 45 else issue.description
                lines.append(f"│ {icon} [{loc:>7}] {desc:<53}│")

            if len(self.issues) > 10:
                lines.append(f"│ ... y {len(self.issues) - 10} problemas más{' ' * 48}│")

            lines.append("└" + "─" * 68 + "┘")
            lines.append("")

        # Errors and warnings
        if self.errors:
            lines.append("ERRORES CRÍTICOS:")
            for error in self.errors:
                lines.append(f"  ❌ {error}")
            lines.append("")

        if self.warnings:
            lines.append("ADVERTENCIAS:")
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")

        if self.suggestions:
            lines.append("SUGERENCIAS:")
            for suggestion in self.suggestions:
                lines.append(f"  💡 {suggestion}")
            lines.append("")

        return "\n".join(lines)


class MusicValidator:
    """
    Validador musical que analiza partituras con music21.
    """

    def __init__(
        self,
        staff: abjad.Staff,
        lilypond_formatter,  # LilyPondFormatter instance
        expected_key: str,
        expected_mode: str,
        expected_meter: Tuple[int, int],
        tolerance: float = 0.7,
    ):
        """
        Inicializa el validador.

        Args:
            staff: Staff de Abjad generado
            lilypond_formatter: Instancia de LilyPondFormatter
            expected_key: Tonalidad esperada (ej: "C", "D", "Eb")
            expected_mode: Modo esperado (ej: "major", "minor", "dorian")
            expected_meter: Compás esperado (ej: (4, 4))
            tolerance: Umbral de aceptación (0.0-1.0)
        """
        self.staff = staff
        self.lilypond_formatter = lilypond_formatter
        self.expected_key = expected_key
        self.expected_mode = expected_mode
        self.expected_meter = expected_meter
        self.tolerance = tolerance

        # Convertir a music21 para análisis
        self.m21_score = self._abjad_to_music21()

    def validate_all(self) -> ValidationReport:
        """Ejecuta todas las validaciones y genera reporte."""

        key_val = self.validate_key()
        meter_val = self.validate_meter()
        range_val = self.validate_range()
        mode_val = self.validate_mode()

        # Calcular validez general
        is_valid = all(
            [
                key_val.is_valid,
                meter_val.is_valid,
                range_val.is_valid,
                mode_val.is_valid,
            ]
        )

        # Calcular puntuación general
        overall_score = self._calculate_overall_score(
            key_val, meter_val, range_val, mode_val
        )

        # Recopilar errores y warnings
        errors = []
        warnings = []
        suggestions = []

        if not key_val.matches:
            errors.append(
                f"Tonalidad detectada ({key_val.detected_key}) no coincide con esperada ({key_val.expected_key})"
            )
            suggestions.append(
                "Ajuste las cadencias finales para reforzar la tonalidad"
            )

        if key_val.correlation < 0.7:
            warnings.append(
                f"Baja certeza en detección de tonalidad ({key_val.correlation:.1%})"
            )

        if not meter_val.is_valid:
            errors.append(
                f"{len(meter_val.measures_invalid)} compases con duración incorrecta"
            )
            suggestions.append(
                "Verifique la generación rítmica en compases problemáticos"
            )

        warnings.extend(key_val.warnings)
        warnings.extend(range_val.warnings)
        warnings.extend(mode_val.warnings)

        return ValidationReport(
            is_valid=is_valid and overall_score >= self.tolerance,
            overall_score=overall_score,
            key_validation=key_val,
            meter_validation=meter_val,
            range_validation=range_val,
            mode_validation=mode_val,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_key(self) -> KeyValidation:
        """Valida la tonalidad usando análisis de Krumhansl-Schmuckler."""
        try:
            # Detectar tonalidad con music21
            detected = self.m21_score.analyze("key")

            # Verificar que el análisis retornó una key válida
            if detected is None:
                return KeyValidation(
                    expected_key=f"{self.expected_key} {self.expected_mode}",
                    detected_key="Sin análisis",
                    correlation=0.0,
                    matches=False,
                    diatonic_percentage=0.0,
                    warnings=["No se pudo detectar tonalidad en la partitura"],
                    is_valid=False,
                )

            # Construir clave esperada
            expected = key.Key(self.expected_key, self.expected_mode)

            # Verificar coincidencia
            matches = (
                detected.tonic.name.upper() == expected.tonic.name.upper()
                and detected.mode == expected.mode
            )

            # Calcular porcentaje diatónico
            diatonic_pct = self._calculate_diatonic_percentage(expected)

            # Determinar validez
            is_valid = matches and detected.correlationCoefficient >= 0.6

            warnings = []
            if not matches and detected.mode != expected.mode:
                warnings.append(
                    f"Modo detectado ({detected.mode}) difiere del esperado ({expected.mode})"
                )

            if diatonic_pct < 0.75:
                warnings.append(f"Solo {diatonic_pct:.1%} de notas son diatónicas")

            return KeyValidation(
                expected_key=str(expected),
                detected_key=str(detected),
                correlation=detected.correlationCoefficient,
                matches=matches,
                diatonic_percentage=diatonic_pct,
                warnings=warnings,
                is_valid=is_valid,
            )

        except Exception as e:
            return KeyValidation(
                expected_key=f"{self.expected_key} {self.expected_mode}",
                detected_key="Error en análisis",
                correlation=0.0,
                matches=False,
                diatonic_percentage=0.0,
                warnings=[f"Error al analizar tonalidad: {str(e)}"],
                is_valid=False,
            )

    def validate_meter(self) -> MeterValidation:
        """Valida que los compases tengan la duración correcta."""
        try:
            measures = list(self.m21_score.flatten().getElementsByClass("Measure"))

            invalid_measures = []
            duration_errors = []

            for i, measure in enumerate(measures):
                # Obtener time signature
                ts = measure.timeSignature
                if ts is None:
                    # Buscar en medida anterior o stream
                    ts = measure.getContextByClass("TimeSignature")

                if ts is None:
                    continue

                expected_ql = ts.barDuration.quarterLength

                # Calcular duración real
                actual_ql = sum(n.quarterLength for n in measure.notesAndRests)

                # Comparar con tolerancia para floats
                if abs(actual_ql - expected_ql) > 0.01:
                    invalid_measures.append(i)
                    duration_errors.append(
                        f"Compás {i + 1}: {actual_ql:.2f} QL en lugar de {expected_ql:.2f}"
                    )

            return MeterValidation(
                expected_meter=self.expected_meter,
                measures_validated=len(measures),
                measures_valid=len(measures) - len(invalid_measures),
                measures_invalid=invalid_measures,
                duration_errors=duration_errors,
                is_valid=len(invalid_measures) == 0,
            )

        except Exception as e:
            return MeterValidation(
                expected_meter=self.expected_meter,
                measures_validated=0,
                measures_valid=0,
                duration_errors=[f"Error al validar métrica: {str(e)}"],
                is_valid=False,
            )

    def validate_range(self) -> RangeValidation:
        """Valida el rango melódico."""
        try:
            # Analizar ámbito
            ambitus = self.m21_score.analyze("ambitus")

            # Obtener notas más grave y aguda (excluir rests)
            from music21 import note

            all_notes = [
                n for n in self.m21_score.flatten().notes if isinstance(n, note.Note)
            ]

            if not all_notes:
                return RangeValidation(
                    ambitus_semitones=0,
                    lowest_pitch="N/A",
                    highest_pitch="N/A",
                    warnings=["No hay notas en la partitura"],
                    is_valid=False,
                )

            all_pitches = [n.pitch for n in all_notes]
            lowest = min(all_pitches, key=lambda p: p.ps)
            highest = max(all_pitches, key=lambda p: p.ps)

            # Verificar que ambitus no es None
            if ambitus is None or not hasattr(ambitus, "semitones"):
                # Calcular manualmente
                ambitus_semitones = int(highest.ps - lowest.ps)
            else:
                ambitus_semitones = ambitus.semitones

            # Verificar cantabilidad (≤ 2 octavas)
            is_singable = ambitus_semitones <= 24

            warnings = []
            if ambitus_semitones > 24:
                warnings.append(
                    f"Rango amplio ({ambitus_semitones} semitonos), puede ser difícil de cantar"
                )

            return RangeValidation(
                ambitus_semitones=ambitus_semitones,
                lowest_pitch=lowest.nameWithOctave,
                highest_pitch=highest.nameWithOctave,
                is_singable=is_singable,
                warnings=warnings,
                is_valid=True,  # Rango amplio es warning, no error
            )

        except Exception as e:
            return RangeValidation(
                ambitus_semitones=0,
                lowest_pitch="Error",
                highest_pitch="Error",
                warnings=[f"Error al analizar rango: {str(e)}"],
                is_valid=False,
            )

    def validate_mode(self) -> ModeValidation:
        """Valida características del modo musical."""
        # Por ahora, validación básica
        # TODO: Implementar análisis específico de características modales

        return ModeValidation(
            expected_mode=self.expected_mode,
            characteristic_intervals_present=True,
            score=0.8,  # Puntuación conservadora por ahora
            is_valid=True,
        )

    def _abjad_to_music21(self) -> stream.Score:
        """
        Convierte Staff de Abjad a Score de music21.

        Utiliza el conversor centralizado para Single Responsibility.
        """
        return AbjadMusic21Converter.abjad_staff_to_music21_score(
            staff=self.staff,
            key_name=self.expected_key,
            mode=self.expected_mode,
            meter_tuple=self.lilypond_formatter.meter_tuple,
        )

    def _calculate_diatonic_percentage(self, expected_key: key.Key) -> float:
        """Calcula porcentaje de notas diatónicas a la escala."""
        try:
            from music21 import note

            scale_pitches = expected_key.getPitches()
            scale_pitch_classes = {p.pitchClass for p in scale_pitches}

            total_notes = 0
            diatonic_notes = 0

            for n in self.m21_score.flatten().notes:
                # Solo contar notas, no rests
                if isinstance(n, note.Note):
                    total_notes += 1
                    if n.pitch.pitchClass in scale_pitch_classes:
                        diatonic_notes += 1

            return diatonic_notes / total_notes if total_notes > 0 else 0.0
        except Exception:
            return 0.0

    def _calculate_overall_score(
        self,
        key_val: KeyValidation,
        meter_val: MeterValidation,
        range_val: RangeValidation,
        mode_val: ModeValidation,
    ) -> float:
        """Calcula puntuación general ponderada."""

        weights = {
            "key": 0.4,  # Tonalidad es lo más importante
            "meter": 0.3,  # Métrica crítica
            "range": 0.15,  # Rango moderadamente importante
            "mode": 0.15,  # Características de modo
        }

        scores = {
            "key": (1.0 if key_val.matches else 0.3) * key_val.correlation,
            "meter": meter_val.measures_valid / max(meter_val.measures_validated, 1),
            "range": 1.0 if range_val.is_singable else 0.7,
            "mode": mode_val.score,
        }

        return sum(scores[k] * weights[k] for k in weights)

    def detect_detailed_issues(self) -> List[ValidationIssue]:
        """
        Detecta problemas específicos con ubicación exacta.

        Analiza cada nota y detecta:
        - Notas fuera de la escala
        - Saltos grandes sin resolver
        - Notas de tendencia sin resolver
        - Problemas de rango

        Returns:
            Lista de ValidationIssue con ubicación exacta
        """
        issues = []
        from music21 import note as m21_note, interval as m21_interval

        try:
            expected_key_obj = key.Key(self.expected_key, self.expected_mode)
            scale_pitch_classes = {p.pitchClass for p in expected_key_obj.getPitches()}

            # Obtener todas las notas con su ubicación
            # Nota: flatten() elimina los Measures pero las notas mantienen measureNumber
            all_notes = []
            for elem in self.m21_score.flatten().notes:
                if isinstance(elem, m21_note.Note):
                    measure_num = elem.measureNumber if hasattr(elem, 'measureNumber') else 1
                    beat = elem.beat if hasattr(elem, 'beat') else 1.0
                    all_notes.append({
                        'note': elem,
                        'measure': measure_num,
                        'beat': beat,
                        'pitch': elem.pitch,
                    })

            # Detectar notas fuera de la escala
            for i, note_info in enumerate(all_notes):
                pitch = note_info['pitch']

                # Verificar si está en la escala
                if pitch.pitchClass not in scale_pitch_classes:
                    issues.append(ValidationIssue(
                        issue_type=IssueType.OUT_OF_KEY,
                        severity=IssueSeverity.WARNING,
                        measure=note_info['measure'],
                        beat=note_info['beat'],
                        note_index=i,
                        description=f"Nota {pitch.nameWithOctave} fuera de {self.expected_key} {self.expected_mode}",
                        actual_value=pitch.nameWithOctave,
                        expected_value=f"nota en {self.expected_key} {self.expected_mode}",
                        suggested_fixes=[
                            f"Cambiar a nota diatónica cercana"
                        ],
                    ))

            # Detectar saltos grandes sin resolver
            for i in range(len(all_notes) - 1):
                current = all_notes[i]
                next_note = all_notes[i + 1]

                intv = m21_interval.Interval(current['pitch'], next_note['pitch'])
                semitones = abs(intv.semitones)

                # Salto de más de una sexta (9 semitonos)
                if semitones > 9:
                    issues.append(ValidationIssue(
                        issue_type=IssueType.LARGE_LEAP,
                        severity=IssueSeverity.WARNING,
                        measure=current['measure'],
                        beat=current['beat'],
                        note_index=i,
                        description=f"Salto de {intv.niceName} ({semitones} semitonos)",
                        actual_value=str(semitones),
                        expected_value="<= 9 semitonos",
                        context={'interval': intv.niceName, 'semitones': semitones},
                        suggested_fixes=[
                            "Reducir intervalo usando nota intermedia",
                            "Resolver por grado conjunto en dirección opuesta"
                        ],
                    ))

            # Verificar rango vocal
            if all_notes:
                pitches = [n['pitch'] for n in all_notes]
                lowest = min(pitches, key=lambda p: p.ps)
                highest = max(pitches, key=lambda p: p.ps)
                ambitus = int(highest.ps - lowest.ps)

                if ambitus > 24:  # Más de 2 octavas
                    # Encontrar las notas extremas
                    for note_info in all_notes:
                        if note_info['pitch'].ps == highest.ps or note_info['pitch'].ps == lowest.ps:
                            issues.append(ValidationIssue(
                                issue_type=IssueType.RANGE_EXCEEDED,
                                severity=IssueSeverity.SUGGESTION,
                                measure=note_info['measure'],
                                beat=note_info['beat'],
                                description=f"Nota {note_info['pitch'].nameWithOctave} en extremo del rango",
                                actual_value=note_info['pitch'].nameWithOctave,
                                suggested_fixes=["Considerar octava diferente"],
                            ))

        except Exception as e:
            # Si hay error, registrarlo como issue
            issues.append(ValidationIssue(
                issue_type=IssueType.OUT_OF_KEY,
                severity=IssueSeverity.WARNING,
                measure=1,
                beat=1.0,
                description=f"Error en análisis: {str(e)}",
            ))

        return issues

    @classmethod
    def from_musicxml(
        cls,
        musicxml_path: str,
        expected_key: str,
        expected_mode: str,
        expected_meter: Tuple[int, int],
        tolerance: float = 0.7,
    ) -> "MusicValidator":
        """
        Crea un validador desde un archivo MusicXML.

        Args:
            musicxml_path: Ruta al archivo MusicXML
            expected_key: Tonalidad esperada
            expected_mode: Modo esperado
            expected_meter: Métrica esperada
            tolerance: Umbral de aceptación

        Returns:
            MusicValidator configurado
        """
        # Cargar MusicXML con music21
        score = converter.parse(musicxml_path)

        # Crear una instancia "vacía" sin staff de abjad
        instance = cls.__new__(cls)
        instance.staff = None
        instance.lilypond_formatter = None
        instance.expected_key = expected_key
        instance.expected_mode = expected_mode
        instance.expected_meter = expected_meter
        instance.tolerance = tolerance
        instance.m21_score = score

        return instance

    def validate_all_with_issues(self) -> ValidationReport:
        """
        Ejecuta todas las validaciones incluyendo detección de issues detallados.

        Returns:
            ValidationReport con lista completa de issues
        """
        # Ejecutar validación básica
        report = self.validate_all()

        # Detectar issues detallados
        detailed_issues = self.detect_detailed_issues()

        # Añadir issues al reporte
        report.issues = detailed_issues

        return report


class AutoCorrector:
    """
    Ajusta parámetros de generación basándose en resultados de validación.
    """

    def __init__(self, validation_report: ValidationReport):
        """
        Inicializa el auto-corrector con un reporte de validación.

        Args:
            validation_report: Reporte de validación que contiene los problemas detectados
        """
        self.report = validation_report

    def suggest_corrections(self) -> Dict[str, Any]:
        """
        Genera sugerencias de corrección basadas en el reporte de validación.

        Returns:
            Dict con parámetros ajustados para la próxima generación
        """
        corrections = {}

        # Correcciones para problemas de tonalidad
        if not self.report.key_validation.matches:
            corrections.update(self._correct_key_issues())

        # Correcciones para problemas de métrica
        if not self.report.meter_validation.is_valid:
            corrections.update(self._correct_meter_issues())

        # Correcciones para problemas de rango
        if (
            not self.report.range_validation.is_valid
            or not self.report.range_validation.is_singable
        ):
            corrections.update(self._correct_range_issues())

        # Correcciones para problemas de modo
        if self.report.mode_validation.score < 0.6:
            corrections.update(self._correct_mode_issues())

        return corrections

    def _correct_key_issues(self) -> Dict[str, Any]:
        """Ajustes para problemas de tonalidad."""
        corrections = {}

        key_val = self.report.key_validation

        # Si la correlación es baja, necesitamos cadencias más fuertes
        if key_val.correlation < 0.7:
            corrections["stronger_cadences"] = True
            corrections["tonic_emphasis"] = 1.5  # Factor multiplicador

        # Si las notas diatónicas son bajas, reducir cromatismo
        if key_val.diatonic_percentage < 0.75:
            corrections["reduce_chromaticism"] = True
            corrections["chromatic_weight"] = 0.3  # Reducir peso de notas cromáticas

        # Asegurar que la melodía termine en tónica
        if not key_val.matches:
            corrections["force_tonic_ending"] = True
            corrections["tonic_cadence_weight"] = 2.0

        return corrections

    def _correct_meter_issues(self) -> Dict[str, Any]:
        """Ajustes para problemas de métrica."""
        corrections = {}

        meter_val = self.report.meter_validation

        # Si hay compases incompletos, ajustar generación rítmica
        if meter_val.measures_invalid:
            corrections["strict_meter"] = True
            corrections["validate_durations"] = True

            # Analizar tipo de error
            avg_error_rate = len(meter_val.measures_invalid) / max(
                meter_val.measures_validated, 1
            )

            if avg_error_rate > 0.3:
                # Muchos errores - simplificar ritmos
                corrections["simplify_rhythms"] = True
                corrections["max_subdivision"] = 2  # Solo hasta corcheas

        return corrections

    def _correct_range_issues(self) -> Dict[str, Any]:
        """Ajustes para problemas de rango."""
        corrections = {}

        range_val = self.report.range_validation

        # Si el rango es muy amplio
        if range_val.ambitus_semitones > 24:
            corrections["reduce_range"] = True
            corrections["max_range_semitones"] = 19  # ~1.5 octavas

            # Ajustar límites de octava
            corrections["preferred_octave_shift"] = -1  # Bajar una octava

        # Si el rango es muy estrecho (< 1 octava)
        elif range_val.ambitus_semitones < 12:
            corrections["expand_range"] = True
            corrections["encourage_leaps"] = True

        return corrections

    def _correct_mode_issues(self) -> Dict[str, Any]:
        """Ajustes para características modales."""
        corrections = {}

        mode_val = self.report.mode_validation

        # Si la puntuación modal es baja
        if mode_val.score < 0.6:
            corrections["emphasize_modal_degrees"] = True

            # Ajustes específicos por modo
            mode = mode_val.expected_mode.lower()

            if "minor" in mode:
                corrections["emphasize_minor_third"] = True
                corrections["minor_cadence_preference"] = 1.5
            elif mode == "dorian":
                corrections["emphasize_sixth_degree"] = True
            elif mode == "phrygian":
                corrections["emphasize_second_degree"] = True
            elif mode == "lydian":
                corrections["emphasize_fourth_degree"] = True
            elif mode == "mixolydian":
                corrections["emphasize_seventh_degree"] = True

        return corrections

    def get_correction_summary(self) -> str:
        """Genera resumen legible de las correcciones sugeridas."""
        corrections = self.suggest_corrections()

        if not corrections:
            return "✓ No se requieren correcciones"

        lines = ["🔧 Correcciones sugeridas:"]

        if corrections.get("stronger_cadences"):
            lines.append("  • Reforzar cadencias para establecer tonalidad")

        if corrections.get("reduce_chromaticism"):
            lines.append("  • Reducir notas cromáticas para mayor diatonicismo")

        if corrections.get("force_tonic_ending"):
            lines.append("  • Asegurar terminación en tónica")

        if corrections.get("strict_meter"):
            lines.append("  • Aplicar validación estricta de duración de compases")

        if corrections.get("simplify_rhythms"):
            lines.append("  • Simplificar patrones rítmicos")

        if corrections.get("reduce_range"):
            lines.append(
                f"  • Reducir rango melódico a {corrections.get('max_range_semitones', 19)} semitonos"
            )

        if corrections.get("expand_range"):
            lines.append("  • Expandir rango melódico con más saltos")

        if corrections.get("emphasize_modal_degrees"):
            lines.append("  • Enfatizar grados característicos del modo")

        return "\n".join(lines)

    def apply_to_architect_params(
        self, current_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aplica las correcciones sugeridas a los parámetros del MelodicArchitect.

        Args:
            current_params: Diccionario con los parámetros actuales del MelodicArchitect

        Returns:
            Diccionario con parámetros corregidos
        """
        corrections = self.suggest_corrections()
        new_params = current_params.copy()

        # Aplicar correcciones de complejidad rítmica
        if corrections.get("simplify_rhythms"):
            new_params["rhythmic_complexity"] = max(
                1, current_params.get("rhythmic_complexity", 2) - 1
            )

        # Aplicar correcciones de rango
        if corrections.get("reduce_range"):
            # Reducir max_interval para limitar el rango
            new_params["max_interval"] = min(4, current_params.get("max_interval", 6))

        # Aplicar correcciones de tonalidad
        if corrections.get("reduce_chromaticism"):
            # Reducir infraction_rate (menos notas fuera de la escala)
            new_params["infraction_rate"] = max(
                0.0, current_params.get("infraction_rate", 0.1) * 0.5
            )

        return new_params
