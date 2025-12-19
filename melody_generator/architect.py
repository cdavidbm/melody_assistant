"""
Clase principal MelodicArchitect.
Orquesta todos los módulos para la generación de melodías.
"""

from typing import Tuple, Optional, List, Union
from dataclasses import dataclass

import abjad

from .models import ImpulseType, MelodicContour, Period
from .config import GenerationConfig, TonalConfig, MeterConfig, RhythmConfig, MelodyConfig, MotifConfig, MarkovConfig, ExpressionConfig
from .scales import ScaleManager
from .harmony import HarmonyManager
from .rhythm import RhythmGenerator
from .pitch import PitchSelector
from .motif import MotifGenerator
from .lilypond import LilyPondFormatter
from .generation import PeriodGenerator
from .loaders import MarkovModelLoader
from .protocols import (
    ScaleManagerProtocol,
    HarmonyManagerProtocol,
    RhythmGeneratorProtocol,
    PitchSelectorProtocol,
    MotifGeneratorProtocol,
    LilyPondFormatterProtocol,
)

# Sistema de expresión modularizado
from .expression_applicator import ExpressionApplicator
from .cadences import CadenceType
from .forms import FormGenerator, FormType, FormPlan

# Módulo de bajo armónico
from .bass import BassGenerator, BassConfig, BassStyle, VoiceLeadingError

# Módulos de memoria, validación y corrección
from .memory import DecisionMemory
from .musicxml import MusicXMLExporter
from .validation import MusicValidator, ValidationReport, IssueType, IssueSeverity
from .correction import SurgicalCorrector, CorrectionRound


class MelodicArchitect:
    """
    Arquitecto melódico basado en teoría musical clásica.

    Implementa el algoritmo "Symmetry & Logic" en tres capas:
    I. Configuración de la Realidad Musical
    II. Generación del ADN (Motivo y Frase)
    III. Desarrollo y Cierre (Período y Cadencia)

    Soporta inyección de dependencias para testing y extensibilidad.
    """

    def __init__(
        self,
        config: Optional[GenerationConfig] = None,
        # Inyección de dependencias (opcionales)
        scale_manager: Optional[ScaleManagerProtocol] = None,
        harmony_manager: Optional[HarmonyManagerProtocol] = None,
        rhythm_generator: Optional[RhythmGeneratorProtocol] = None,
        pitch_selector: Optional[PitchSelectorProtocol] = None,
        motif_generator: Optional[MotifGeneratorProtocol] = None,
        lilypond_formatter: Optional[LilyPondFormatterProtocol] = None,
        # Parámetros legacy para compatibilidad
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
        max_interval: int = 6,
        use_tenoris: bool = False,
        tenoris_probability: float = 0.2,
        variation_freedom: int = 2,
        use_markov: bool = False,
        markov_composer: str = "bach",
        markov_weight: float = 0.3,
        markov_order: int = 2,
        # Nuevos parámetros de expresión
        expression_config: Optional[ExpressionConfig] = None,
        use_ornamentation: bool = False,
        ornamentation_style: str = "classical",
        use_dynamics: bool = True,
        use_articulations: bool = True,
    ):
        """
        Inicializa el arquitecto melódico.

        Puede recibir:
        1. Un objeto GenerationConfig para configuración centralizada
        2. Parámetros individuales para compatibilidad con API anterior
        3. Dependencias inyectadas para testing o extensibilidad

        Args:
            config: Configuración centralizada (opcional)
            scale_manager: Gestor de escalas inyectado (opcional)
            harmony_manager: Gestor armónico inyectado (opcional)
            rhythm_generator: Generador rítmico inyectado (opcional)
            pitch_selector: Selector de tonos inyectado (opcional)
            motif_generator: Generador de motivos inyectado (opcional)
            lilypond_formatter: Formateador LilyPond inyectado (opcional)
            key_name: Tonalidad (legacy)
            mode: Modo musical (legacy)
            ... otros parámetros legacy
        """
        # Si no se proporciona config, crear desde parámetros legacy
        if config is None:
            config = GenerationConfig.from_simple_params(
                key_name=key_name,
                mode=mode,
                meter_tuple=meter_tuple,
                subdivisions=subdivisions,
                num_measures=num_measures,
                impulse_type=impulse_type,
                infraction_rate=infraction_rate,
                rhythmic_complexity=rhythmic_complexity,
                use_rests=use_rests,
                rest_probability=rest_probability,
                use_motivic_variations=use_motivic_variations,
                variation_probability=variation_probability,
                climax_position=climax_position,
                climax_intensity=climax_intensity,
                max_interval=max_interval,
                use_tenoris=use_tenoris,
                tenoris_probability=tenoris_probability,
                variation_freedom=variation_freedom,
                use_markov=use_markov,
                markov_composer=markov_composer,
                markov_weight=markov_weight,
                markov_order=markov_order,
            )

        self.config = config

        # Exponer propiedades para compatibilidad
        self.key_name = config.tonal.key_name
        self.mode = config.tonal.mode
        self.meter_tuple = config.meter.meter_tuple
        self.subdivisions = config.meter.subdivisions
        self.num_measures = config.meter.num_measures
        self.impulse_type = config.melody.impulse_type

        # Crear contorno melódico
        self.contour = MelodicContour(
            climax_position=config.melody.climax_position,
            climax_emphasis=config.melody.climax_intensity,
        )

        # Cargar modelos de Markov usando el loader centralizado
        melody_markov, rhythm_markov = MarkovModelLoader.load_all(config.markov)

        # Inicializar componentes (usar inyectados o crear nuevos)
        self.scale_manager = scale_manager or ScaleManager(
            config.tonal.key_name, config.tonal.mode
        )

        self.rhythm_generator = rhythm_generator or RhythmGenerator(
            meter_tuple=config.meter.meter_tuple,
            subdivisions=config.meter.subdivisions,
            rhythmic_complexity=config.rhythm.complexity,
            num_measures=config.meter.num_measures,
            markov_model=rhythm_markov,
            markov_weight=config.markov.weight,
        )

        self.harmony_manager = harmony_manager or HarmonyManager(
            mode=config.tonal.mode,
            num_measures=config.meter.num_measures,
            strong_beats=self.rhythm_generator.strong_beats,
        )

        self.pitch_selector = pitch_selector or PitchSelector(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            contour=self.contour,
            num_measures=config.meter.num_measures,
            max_interval=config.melody.max_interval,
            use_tenoris=config.melody.use_tenoris,
            tenoris_probability=config.melody.tenoris_probability,
            infraction_rate=config.melody.infraction_rate,
            use_rests=config.rhythm.use_rests,
            rest_probability=config.rhythm.rest_probability,
            impulse_type=config.melody.impulse_type,
            meter_tuple=config.meter.meter_tuple,
            markov_model=melody_markov,
            markov_weight=config.markov.weight,
        )

        climax_measure = int(config.meter.num_measures * config.melody.climax_position)
        self.motif_generator = motif_generator or MotifGenerator(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            rhythmic_complexity=config.rhythm.complexity,
            variation_freedom=config.motif.variation_freedom,
            use_motivic_variations=config.motif.use_motivic_variations,
            variation_probability=config.motif.variation_probability,
            contour=self.contour,
            climax_measure=climax_measure,
        )

        self.lilypond_formatter = lilypond_formatter or LilyPondFormatter(
            scale_manager=self.scale_manager,
            mode=config.tonal.mode,
            meter_tuple=config.meter.meter_tuple,
            impulse_type=config.melody.impulse_type,
        )

        self.period_generator = PeriodGenerator(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            rhythm_generator=self.rhythm_generator,
            pitch_selector=self.pitch_selector,
            motif_generator=self.motif_generator,
            lilypond_formatter=self.lilypond_formatter,
            num_measures=config.meter.num_measures,
            meter_tuple=config.meter.meter_tuple,
            impulse_type=config.melody.impulse_type,
        )

        # Configuración de expresión
        if expression_config is None:
            expression_config = ExpressionConfig(
                use_ornamentation=use_ornamentation,
                ornamentation_style=ornamentation_style,
                use_dynamics=use_dynamics,
                use_articulations=use_articulations,
            )
        self.expression_config = expression_config

        # Inicializar aplicador de expresiones (modularizado)
        self.expression_applicator = ExpressionApplicator(
            config=expression_config,
            key_name=config.tonal.key_name,
            mode=config.tonal.mode,
            num_measures=config.meter.num_measures,
            scale_pitches=self.scale_manager.get_scale_pitches(),
        )

        # Exponer generadores para compatibilidad con API existente
        self.ornament_generator = self.expression_applicator.ornament_generator
        self.dynamic_generator = self.expression_applicator.dynamic_generator
        self.articulation_generator = self.expression_applicator.articulation_generator
        self.cadence_generator = self.expression_applicator.cadence_generator
        self.form_generator = self.expression_applicator.form_generator
        self.modulation_generator = self.expression_applicator.modulation_generator
        self.motivic_developer = self.expression_applicator.motivic_developer
        self.sequence_generator = self.expression_applicator.sequence_generator

    @classmethod
    def from_config(cls, config: GenerationConfig) -> "MelodicArchitect":
        """
        Factory method para crear desde configuración.

        Args:
            config: Configuración completa

        Returns:
            Nueva instancia de MelodicArchitect
        """
        return cls(config=config)

    @classmethod
    def with_defaults(cls) -> "MelodicArchitect":
        """
        Factory method para crear con valores por defecto.

        Returns:
            Nueva instancia de MelodicArchitect con configuración por defecto
        """
        return cls(config=GenerationConfig())

    def generate_period(self) -> abjad.Staff:
        """
        Genera un período musical completo (método tradicional).

        Returns:
            abjad.Staff con la melodía generada
        """
        return self.period_generator.generate_period()

    def generate_period_hierarchical(
        self, return_structure: bool = False
    ) -> Union[abjad.Staff, Tuple[abjad.Staff, Period]]:
        """
        Genera un período musical con jerarquía formal verdadera.

        Construye una estructura Period completa (con Phrase y Semiphrase)
        antes de renderizar a Abjad, permitiendo análisis estructural.

        Args:
            return_structure: Si True, retorna también la estructura Period

        Returns:
            abjad.Staff con la melodía, o tupla (Staff, Period) si return_structure=True
        """
        return self.period_generator.generate_period_hierarchical(
            return_structure=return_structure
        )

    def generate_period_genetic(
        self,
        generations: int = 15,
        population_size: int = 30,
        use_markov_polish: bool = True,
        return_structure: bool = False,
    ) -> Union[abjad.Staff, Tuple[abjad.Staff, Period]]:
        """
        Genera un período musical usando algoritmos genéticos.

        El GA evoluciona el motivo base optimizando múltiples criterios:
        - Conducción de voces (preferir grados conjuntos)
        - Compatibilidad armónica (notas del acorde en tiempos fuertes)
        - Calidad del contorno (forma melódica interesante)
        - Interés rítmico (variedad sin caos)
        - Potencial de desarrollo (facilidad de variación)
        - Equilibrio de rango (dentro del ámbito cantable)

        El motivo evolucionado se desarrolla en un período completo
        usando variaciones motívicas (inversión, retrogradación, etc.).

        Opcionalmente, Markov puede pulir el resultado final.

        Args:
            generations: Número de generaciones GA (10-30 recomendado)
            population_size: Tamaño de población (20-50 recomendado)
            use_markov_polish: Si aplicar pulido Markov al final
            return_structure: Si True, retorna también la estructura Period

        Returns:
            abjad.Staff con la melodía evolucionada,
            o tupla (Staff, Period) si return_structure=True
        """
        from .genetic import GeneticMelodyEvolver, GeneticConfig

        # Configurar evolucionador genético
        genetic_config = GeneticConfig(
            enabled=True,
            generations=generations,
            population_size=population_size,
            use_markov_polish=use_markov_polish,
        )

        evolver = GeneticMelodyEvolver(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            config=genetic_config,
        )

        # Evolucionar y desarrollar período
        period, evolved_chromosome = evolver.evolve_and_develop(
            total_measures=self.num_measures
        )

        # Renderizar período a Staff usando period_generator
        staff = self._render_genetic_period_to_staff(period)

        # Aplicar pulido Markov si está habilitado y hay modelo
        if use_markov_polish and self.config.markov.enabled:
            staff = self._apply_markov_polish(staff)

        if return_structure:
            return staff, period
        return staff

    def _render_genetic_period_to_staff(self, period: Period) -> abjad.Staff:
        """
        Renderiza un Period genético a abjad.Staff.

        Args:
            period: Estructura Period generada por GA

        Returns:
            abjad.Staff con la melodía
        """
        notes = []

        # Obtener todos los motivos del período
        all_motifs = period.get_all_motifs()

        for motif in all_motifs:
            for i, (pitch_str, duration) in enumerate(
                zip(motif.pitches, motif.rhythm.durations)
            ):
                # Convertir pitch a formato LilyPond
                lily_pitch = self.lilypond_formatter.convert_to_abjad_pitch(pitch_str)

                # Crear duración string para Abjad
                num, denom = duration
                if num == 1:
                    dur_str = str(denom)
                elif num == 3 and denom % 2 == 0:
                    # Duración con puntillo (3/8 -> 4.)
                    dur_str = f"{denom // 2}."
                else:
                    # Casos especiales
                    dur_str = str(denom)

                # Crear nota combinando pitch y duración
                note = abjad.Note(f"{lily_pitch}{dur_str}")
                notes.append(note)

        # Crear staff con signatura de tiempo
        staff = abjad.Staff(notes)
        time_sig = abjad.TimeSignature(self.meter_tuple)
        abjad.attach(time_sig, staff[0])

        return staff

    def _apply_markov_polish(self, staff: abjad.Staff) -> abjad.Staff:
        """
        Aplica pulido Markov al staff para suavizar voice leading.

        Nota: Esta es una implementación simplificada.
        El pulido completo requeriría acceso a modelos Markov
        y análisis más profundo.

        Args:
            staff: Staff a pulir

        Returns:
            Staff con ajustes menores de voice leading
        """
        # Por ahora, retornar sin modificación
        # El pulido completo se implementará en una versión futura
        return staff

    def generate_period_with_bass(
        self,
        bass_style: BassStyle = BassStyle.SIMPLE,
        bass_config: Optional[BassConfig] = None,
        return_staffs: bool = False,
        verify_voice_leading: bool = True,
    ) -> Union[str, Tuple[abjad.Staff, abjad.Staff, List[VoiceLeadingError]]]:
        """
        Genera un período musical con línea de bajo armónico.

        Crea dos staffs:
        - Melodía (clave de Sol) generada con los métodos existentes
        - Bajo (clave de Fa) siguiendo la progresión armónica

        El bajo puede ser:
        - Simple: una nota por compás (unidad de compás)
        - Alberti: arpegio del acorde
        - Walking: movimiento diatónico por grados conjuntos

        Args:
            bass_style: Estilo de bajo (SIMPLE, ALBERTI, WALKING)
            bass_config: Configuración opcional del bajo
            return_staffs: Si True, retorna los staffs individuales
            verify_voice_leading: Si True, verifica conducción de voces

        Returns:
            String con código LilyPond (PianoStaff),
            o tupla (melody_staff, bass_staff, errors) si return_staffs=True
        """
        # Crear configuración de bajo si no se proporciona
        if bass_config is None:
            bass_config = BassConfig(style=bass_style)
        else:
            bass_config.style = bass_style

        # Generar melodía
        melody_staff = self.generate_period()

        # Extraer pitches MIDI de la melodía para que el bajo conozca la melodía
        melody_pitches = self._extract_melody_pitches(melody_staff)

        # Crear generador de bajo
        bass_generator = BassGenerator(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            meter_tuple=self.meter_tuple,
            config=bass_config,
            impulse_type=self.impulse_type,
            anacrusis_duration=self.lilypond_formatter.anacrusis_duration,
        )

        # Obtener progresión armónica
        harmonic_plan = self.harmony_manager.create_harmonic_progression(
            self.num_measures
        )

        # Generar bajo CON conocimiento de la melodía
        bass_staff = bass_generator.generate_bass_line(harmonic_plan, melody_pitches)

        # CORRECCIÓN POST-GENERACIÓN: Eliminar disonancias fuertes
        # Analiza qué notas suenan simultáneamente y corrige 2das/7mas
        dissonance_fixes = bass_generator.fix_dissonances_post_generation(
            bass_staff, melody_staff
        )

        # Aplicar expresión al bajo (dinámicas, articulaciones, slurs)
        bass_staff = bass_generator.apply_expression(bass_staff, self.num_measures)

        # Verificar y corregir conducción de voces (quintas/octavas paralelas)
        voice_leading_errors = []
        if verify_voice_leading:
            voice_leading_errors = bass_generator.verify_voice_leading(
                bass_staff, melody_staff
            )

        if return_staffs:
            return melody_staff, bass_staff, voice_leading_errors

        # Formatear como LilyPond polyphonic
        lily_code = self.lilypond_formatter.format_output_polyphonic(
            melody_staff=melody_staff,
            bass_staff=bass_staff,
        )

        return lily_code

    def generate_period_with_bass_and_expression(
        self,
        bass_style: BassStyle = BassStyle.SIMPLE,
        bass_config: Optional[BassConfig] = None,
        title: Optional[str] = None,
        composer: Optional[str] = None,
    ) -> str:
        """
        Genera período con bajo y expresiones aplicadas.

        Combina generación de bajo con dinámicas, articulaciones, etc.

        Args:
            bass_style: Estilo de bajo
            bass_config: Configuración del bajo
            title: Título opcional
            composer: Compositor opcional

        Returns:
            String con código LilyPond (PianoStaff con expresiones)
        """
        melody_staff, bass_staff, errors = self.generate_period_with_bass(
            bass_style=bass_style,
            bass_config=bass_config,
            return_staffs=True,
        )

        # Aplicar expresiones a la melodía
        melody_staff = self.apply_expression(melody_staff)

        # Formatear como LilyPond polyphonic
        lily_code = self.lilypond_formatter.format_output_polyphonic(
            melody_staff=melody_staff,
            bass_staff=bass_staff,
            title=title,
            composer=composer,
        )

        return lily_code

    def format_as_lilypond_polyphonic(
        self,
        melody_staff: abjad.Staff,
        bass_staff: abjad.Staff,
        title: Optional[str] = None,
        composer: Optional[str] = None,
    ) -> str:
        """
        Formatea melodía y bajo existentes como código LilyPond.

        Args:
            melody_staff: Staff con la melodía
            bass_staff: Staff con el bajo
            title: Título opcional
            composer: Compositor opcional

        Returns:
            String con código LilyPond (PianoStaff)
        """
        return self.lilypond_formatter.format_output_polyphonic(
            melody_staff=melody_staff,
            bass_staff=bass_staff,
            title=title,
            composer=composer,
        )

    def generate_and_display(
        self,
        output_format: str = "lilypond",
        title: Optional[str] = None,
        composer: Optional[str] = None,
    ) -> str:
        """
        Genera el período y retorna la representación en formato LilyPond.

        Args:
            output_format: "lilypond" para código LilyPond, "show" para visualizar
            title: Título opcional de la pieza
            composer: Compositor opcional

        Returns:
            String con código LilyPond
        """
        partitura = self.generate_period()

        if output_format == "show":
            abjad.show(partitura)
            return "Partitura mostrada"
        else:
            return self.lilypond_formatter.format_output(
                partitura, title=title, composer=composer
            )

    def format_as_lilypond(
        self,
        staff: abjad.Staff,
        title: Optional[str] = None,
        composer: Optional[str] = None,
    ) -> str:
        """
        Formatea un staff existente como código LilyPond.

        Args:
            staff: Staff de Abjad a formatear
            title: Título opcional
            composer: Compositor opcional

        Returns:
            String con código LilyPond
        """
        return self.lilypond_formatter.format_output(
            staff, title=title, composer=composer
        )

    def apply_expression(self, staff: abjad.Staff) -> abjad.Staff:
        """
        Aplica características expresivas a un staff generado.

        Delega al ExpressionApplicator modularizado.

        Args:
            staff: Staff de Abjad con la melodía

        Returns:
            Staff con dinámicas, articulaciones y ornamentos aplicados
        """
        return self.expression_applicator.apply(staff)

    def generate_period_with_expression(self) -> abjad.Staff:
        """
        Genera un período musical con características expresivas aplicadas.

        Returns:
            abjad.Staff con melodía, dinámicas, articulaciones, etc.
        """
        staff = self.generate_period()
        return self.apply_expression(staff)

    def generate_with_validation(
        self,
        target_score: float = 0.80,
        max_rounds: int = 5,
        min_improvement: float = 0.02,
        apply_expressions: bool = True,
        verbose: bool = True,
    ) -> Tuple[abjad.Staff, ValidationReport, DecisionMemory]:
        """
        Genera un período con validación y corrección quirúrgica iterativa.

        Este método:
        1. Genera la melodía registrando todas las decisiones
        2. Exporta a MusicXML temporal para validación
        3. Valida con music21 detectando issues específicos
        4. Si score < target, aplica correcciones quirúrgicas
        5. Repite hasta alcanzar score o agotar intentos

        Args:
            target_score: Score objetivo (default 80%)
            max_rounds: Máximo de rondas de corrección (default 5)
            min_improvement: Mejora mínima para continuar (default 2%)
            apply_expressions: Si aplicar expresiones al final
            verbose: Si mostrar progreso

        Returns:
            Tupla (staff, validation_report, decision_memory)
        """
        # Inicializar memoria de decisiones
        memory = DecisionMemory()
        memory.set_metadata(
            key_name=self.key_name,
            mode=self.mode,
            meter=self.meter_tuple,
            num_measures=self.num_measures,
        )

        # Configurar pitch_selector con memoria
        self.pitch_selector.set_decision_memory(memory)
        self.pitch_selector.reset_for_new_generation()

        # Generar melodía inicial
        if verbose:
            print("Generando melodía inicial...")
        staff = self.generate_period()

        # Inicializar exportador MusicXML
        exporter = MusicXMLExporter()

        # Loop de validación y corrección
        current_round = 0
        final_report = None
        corrector = None

        while True:
            # Exportar a MusicXML temporal
            musicxml_path = exporter.export_for_validation(
                staff=staff,
                key_name=self.key_name,
                mode=self.mode,
                meter_tuple=self.meter_tuple,
            )

            # Validar con music21
            validator = MusicValidator.from_musicxml(
                musicxml_path=musicxml_path,
                expected_key=self.key_name,
                expected_mode=self.mode,
                expected_meter=self.meter_tuple,
                tolerance=target_score,
            )
            report = validator.validate_all_with_issues()

            if verbose:
                status = "✓" if report.overall_score >= target_score else "⚠"
                print(f"  {status} Ronda {current_round}: Score = {report.overall_score:.1%}")
                if report.issues:
                    print(f"    Issues: {len(report.issues)} ({len(report.get_critical_issues())} críticos)")

            # Verificar si alcanzamos el objetivo
            if report.overall_score >= target_score:
                if verbose:
                    print(f"  ✓ Score objetivo alcanzado: {report.overall_score:.1%}")
                final_report = report
                break

            # Verificar si debemos continuar
            if current_round >= max_rounds:
                if verbose:
                    print(f"  ⚠ Máximo de rondas alcanzado. Score final: {report.overall_score:.1%}")
                final_report = report
                break

            # Verificar rendimientos decrecientes
            if corrector and current_round > 1:
                should_continue, reason = corrector.should_continue(
                    current_score=report.overall_score,
                    target_score=target_score,
                    max_rounds=max_rounds,
                    min_improvement=min_improvement,
                )
                if not should_continue:
                    if verbose:
                        print(f"  ⚠ Detenido: {reason}. Score final: {report.overall_score:.1%}")
                    final_report = report
                    break

            # Inicializar corrector si es necesario
            if corrector is None:
                corrector = SurgicalCorrector(
                    staff=staff,
                    memory=memory,
                    key_name=self.key_name,
                    mode=self.mode,
                )

            # Intentar correcciones
            critical_issues = report.get_critical_issues()
            warning_issues = report.get_issues_by_severity(IssueSeverity.WARNING)

            # Priorizar issues críticos, luego warnings
            issues_to_fix = critical_issues + warning_issues[:5]

            if not issues_to_fix:
                if verbose:
                    print(f"  ⚠ No hay issues corregibles. Score final: {report.overall_score:.1%}")
                final_report = report
                break

            if verbose:
                print(f"    Intentando corregir {len(issues_to_fix)} issues...")

            correction_round = corrector.fix_issues(
                issues=issues_to_fix,
                score_before=report.overall_score,
            )

            if correction_round.issues_fixed == 0:
                if verbose:
                    print(f"  ⚠ No se pudo corregir ningún issue. Score final: {report.overall_score:.1%}")
                final_report = report
                break

            if verbose:
                print(f"    Corregidos: {correction_round.issues_fixed}/{correction_round.issues_attempted}")

            current_round += 1

        # Limpiar archivo temporal
        exporter.cleanup()

        # Aplicar expresiones si se solicitó
        if apply_expressions:
            staff = self.apply_expression(staff)

        return staff, final_report, memory

    def generate_with_form(
        self,
        form_type: str = "binary",
    ) -> List[abjad.Staff]:
        """
        Genera múltiples secciones según una forma musical.

        Args:
            form_type: "binary", "ternary", "rondo", "theme_var"

        Returns:
            Lista de Staffs, uno por sección
        """
        # Crear plan formal
        form_map = {
            "binary": self.form_generator.create_binary_form,
            "ternary": self.form_generator.create_ternary_form,
            "rondo": lambda: self.form_generator.create_rondo_form(num_episodes=2),
            "theme_var": lambda: self.form_generator.create_theme_and_variations(num_variations=3),
        }

        creator = form_map.get(form_type, self.form_generator.create_binary_form)
        plan = creator()

        staffs = []
        for section in plan.sections:
            # Crear nuevo arquitecto para cada sección si cambia tonalidad
            if section.key_name != self.key_name or section.mode != self.mode:
                section_architect = MelodicArchitect(
                    key_name=section.key_name,
                    mode=section.mode,
                    meter_tuple=self.meter_tuple,
                    num_measures=section.num_measures,
                    expression_config=self.expression_config,
                )
                section_staff = section_architect.generate_period_with_expression()
            else:
                # Usar configuración actual
                original_measures = self.num_measures
                self.num_measures = section.num_measures
                section_staff = self.generate_period_with_expression()
                self.num_measures = original_measures

            staffs.append(section_staff)

        return staffs

    def get_cadence_gesture(
        self,
        cadence_type: str = "authentic",
        is_final: bool = True,
    ) -> dict:
        """
        Obtiene el gesto melódico para una cadencia específica.

        Delega al ExpressionApplicator.

        Args:
            cadence_type: "authentic", "half", "deceptive", "plagal"
            is_final: Si es cadencia final

        Returns:
            Dict con grados melódicos y duraciones
        """
        return self.expression_applicator.get_cadence_gesture(cadence_type, is_final)

    def get_modulation_plan(
        self,
        target_relationship: str = "dominant",
    ) -> dict:
        """
        Obtiene un plan de modulación a una tonalidad relacionada.

        Delega al ExpressionApplicator.

        Args:
            target_relationship: "dominant", "relative", "subdominant", "parallel"

        Returns:
            Dict con información de la modulación
        """
        return self.expression_applicator.get_modulation_plan(target_relationship)

    def _extract_melody_pitches(self, staff: abjad.Staff) -> List[int]:
        """
        Extrae los pitches MIDI de un staff de melodía.

        Esto permite que el bajo CONOZCA la melodía y pueda:
        - Evitar disonancias en tiempos fuertes
        - Crear movimiento contrario cuando sea apropiado
        - Verificar consonancias en tiempo real

        Args:
            staff: Staff de Abjad con la melodía

        Returns:
            Lista de valores MIDI de cada nota
        """
        pitches = []
        for leaf in abjad.iterate.leaves(staff):
            if isinstance(leaf, abjad.Note):
                pitch = leaf.written_pitch
                if callable(pitch):
                    pitch = pitch()
                # Abjad: pitch.number es relativo a C4 (middle C)
                pitch_num = pitch.number
                if callable(pitch_num):
                    pitch_num = pitch_num()
                midi_value = pitch_num + 60  # C4 = MIDI 60
                pitches.append(midi_value)
            elif isinstance(leaf, abjad.Rest):
                # Para silencios, usar el pitch anterior o un valor neutro
                if pitches:
                    pitches.append(pitches[-1])
                else:
                    pitches.append(60)  # C4 como default
        return pitches
