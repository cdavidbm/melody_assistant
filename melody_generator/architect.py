"""
Clase principal MelodicArchitect.
Orquesta todos los módulos para la generación de melodías.
"""

from typing import Tuple, Optional, List, Union
from dataclasses import dataclass

import abjad

from .models import ImpulseType, MelodicContour, Period, HarmonicFunction
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

    def develop_user_motif(
        self,
        user_motif: str,
        num_measures: int = 8,
        variation_freedom: int = 2,
        detect_key: bool = True,
        add_bass: bool = False,
        title: str = "Desarrollo de Idea",
        composer: str = "CompositorIA",
    ) -> Tuple[abjad.Staff, str]:
        """
        Desarrolla un motivo proporcionado por el usuario.

        El sistema toma el motivo del usuario como base y lo desarrolla
        aplicando variaciones motívicas, sin cambiar la idea original.

        Args:
            user_motif: Notación LilyPond del motivo (e.g., "c'4 d' e' f'")
            num_measures: Número de compases a generar
            variation_freedom: 1=conservador, 2=moderado, 3=creativo
            detect_key: Si True, intenta detectar la tonalidad del motivo
            add_bass: Si True, agrega línea de bajo
            title: Título para la partitura
            composer: Nombre del compositor

        Returns:
            Tuple[Staff, str]: Staff con la melodía desarrollada y código LilyPond
        """
        import re

        # Parse LilyPond notation to extract notes
        notes_from_input = self._parse_lilypond_motif(user_motif)

        if not notes_from_input:
            raise ValueError(
                "No se pudieron extraer notas del motivo. "
                "Usa formato LilyPond: c'4 d' e' f' (nota + octava + duración)"
            )

        # Detect key if requested
        if detect_key:
            detected_key, detected_mode = self._analyze_motif_key(notes_from_input)
            # Update scale manager with detected key
            self.scale_manager = ScaleManager(detected_key, detected_mode)
            self.key_name = detected_key
            self.mode = detected_mode
            # Update num_measures for the development
            self.num_measures = num_measures

        # Create the original motif as Abjad notes
        original_notes = []
        for note_data in notes_from_input:
            pitch_str = note_data["pitch"]
            duration_str = note_data["duration"]
            try:
                note = abjad.Note(f"{pitch_str}{duration_str}")
                original_notes.append(note)
            except Exception:
                # Skip malformed notes
                continue

        if not original_notes:
            raise ValueError("No se pudieron crear notas válidas del motivo")

        # Calculate how many times to use the motif and variations
        # to fill the requested measures
        meter_num, meter_den = self.meter_tuple
        beats_per_measure = meter_num * (4 / meter_den)
        total_beats = beats_per_measure * num_measures

        # Calculate duration of original motif
        motif_duration = 0
        for n in original_notes:
            dur = abjad.get.duration(n)
            # Duration can be accessed as a fraction
            motif_duration += float(dur) * 4  # Convert to beats (quarter = 1)

        # Build the piece
        import copy
        all_notes = []

        # Start with original motif
        for note in original_notes:
            all_notes.append(copy.deepcopy(note))

        current_beats = motif_duration

        # Define variation types based on freedom level
        if variation_freedom == 1:
            variation_types = ["RHYTHMIC_AUGMENTATION", "RHYTHMIC_DIMINUTION"]
        elif variation_freedom == 2:
            variation_types = [
                "RHYTHMIC_AUGMENTATION",
                "RHYTHMIC_DIMINUTION",
                "INTERVALIC_EXPANSION",
                "TRANSPOSITION",
            ]
        else:
            variation_types = [
                "RHYTHMIC_AUGMENTATION",
                "RHYTHMIC_DIMINUTION",
                "INTERVALIC_EXPANSION",
                "INTERVALIC_CONTRACTION",
                "MELODIC_INVERSION",
                "RETROGRADE",
                "TRANSPOSITION",
            ]

        # Generate variations until we fill the measures
        iteration = 0
        max_iterations = 50  # Safety limit

        while current_beats < total_beats and iteration < max_iterations:
            iteration += 1

            # Choose a variation type
            import random
            var_type = random.choice(variation_types)

            # Apply variation to create new notes
            varied_notes = self._apply_motif_variation(
                original_notes, var_type, iteration
            )

            # Add to result
            for note in varied_notes:
                if current_beats >= total_beats:
                    break
                all_notes.append(note)
                note_beats = float(abjad.get.duration(note)) * 4
                current_beats += note_beats

        # Create staff
        staff = abjad.Staff(all_notes)

        # Add time signature and key signature
        time_sig = abjad.TimeSignature(self.meter_tuple)
        abjad.attach(time_sig, staff[0])

        key_sig = self._create_key_signature()
        if key_sig:
            abjad.attach(key_sig, staff[0])

        # Generate LilyPond code
        if add_bass:
            # Generate bass line
            melody_pitches = self._extract_melody_pitches(staff)
            bass_config = BassConfig(style=BassStyle.SIMPLE, octave=3)

            bass_generator = BassGenerator(
                scale_manager=self.scale_manager,
                harmony_manager=self.harmony_manager,
                meter_tuple=self.meter_tuple,
                config=bass_config,
            )

            # Create a simple harmonic plan based on measures
            harmonic_plan = self._create_simple_harmonic_plan(num_measures)

            bass_staff = bass_generator.generate_bass_line(
                harmonic_plan=harmonic_plan,
                melody_pitches=melody_pitches,
            )

            # Format as piano staff
            lilypond_code = self.format_as_lilypond_polyphonic(
                melody_staff=staff,
                bass_staff=bass_staff,
                title=title,
                composer=composer,
            )
        else:
            lilypond_code = self.format_as_lilypond(
                staff,
                title=title,
                composer=composer,
            )

        return staff, lilypond_code

    def develop_user_motif_v2(
        self,
        original_lilypond: str,
        music21_stream,  # music21.stream.Stream from validation
        num_measures: int = 8,
        variation_freedom: int = 2,
        add_bass: bool = False,
        title: str = "Desarrollo de Idea",
        composer: str = "CompositorIA",
    ) -> Tuple[abjad.Staff, str]:
        """
        Desarrolla un motivo preservando el LilyPond original LITERALMENTE.

        Esta versión V2 soluciona el bug crítico donde el motivo del usuario
        era ignorado. Ahora:
        1. El LilyPond original se preserva exactamente como el usuario lo escribió
        2. El stream music21 se usa SOLO para análisis (intervalos, contorno, ritmo)
        3. Solo se genera material de DESARROLLO para los compases restantes
        4. Output = LilyPond original + desarrollo generado

        Args:
            original_lilypond: Notación LilyPond EXACTA del usuario (se preserva literal)
            music21_stream: Stream de music21 del motivo (para análisis, no modificación)
            num_measures: Número total de compases a generar
            variation_freedom: 1=conservador, 2=moderado, 3=creativo
            add_bass: Si True, agrega línea de bajo
            title: Título para la partitura
            composer: Nombre del compositor

        Returns:
            Tuple[Staff, str]: Staff con la melodía y código LilyPond completo
        """
        import copy
        import random
        from music21 import note as m21note, pitch as m21pitch

        # ═══════════════════════════════════════════════════════════════════
        # PASO 1: Analizar el motivo con music21 (SIN MODIFICAR)
        # ═══════════════════════════════════════════════════════════════════

        # Extraer información del motivo para desarrollo
        motif_notes = []
        motif_intervals = []
        motif_rhythms = []
        last_pitch = None

        for element in music21_stream.flatten().notesAndRests:
            if isinstance(element, m21note.Note):
                motif_notes.append({
                    'pitch': element.pitch.midi,
                    'duration': element.quarterLength,
                    'pitch_name': element.pitch.nameWithOctave,
                })
                motif_rhythms.append(element.quarterLength)

                if last_pitch is not None:
                    interval = element.pitch.midi - last_pitch
                    motif_intervals.append(interval)
                last_pitch = element.pitch.midi

            elif isinstance(element, m21note.Rest):
                motif_rhythms.append(element.quarterLength)

        # Calcular duración total del motivo en beats
        motif_total_beats = sum(motif_rhythms)

        # Calcular cuántos compases ocupa el motivo
        meter_num, meter_den = self.meter_tuple
        beats_per_measure = meter_num * (4 / meter_den)
        motif_measures = motif_total_beats / beats_per_measure

        # Calcular compases de desarrollo necesarios
        development_measures = max(0, num_measures - motif_measures)
        development_beats = development_measures * beats_per_measure

        if development_beats <= 0:
            # El motivo ya llena todo, no hay desarrollo
            # Solo formateamos el original
            return self._format_original_only(
                original_lilypond, title, composer, add_bass, num_measures
            )

        # ═══════════════════════════════════════════════════════════════════
        # PASO 2: Extraer características para desarrollo
        # ═══════════════════════════════════════════════════════════════════

        # Rango melódico del motivo
        if motif_notes:
            pitches = [n['pitch'] for n in motif_notes]
            motif_min_pitch = min(pitches)
            motif_max_pitch = max(pitches)
            motif_center = (motif_min_pitch + motif_max_pitch) // 2
            last_motif_pitch = pitches[-1]
            first_motif_pitch = pitches[0]
        else:
            motif_center = 60  # C4
            last_motif_pitch = 60
            first_motif_pitch = 60
            motif_min_pitch = 55
            motif_max_pitch = 72

        # Intervalos característicos
        characteristic_intervals = list(set(motif_intervals)) if motif_intervals else [0, 2, -2]

        # Ritmos característicos
        characteristic_rhythms = list(set(motif_rhythms)) if motif_rhythms else [1.0]

        # ═══════════════════════════════════════════════════════════════════
        # PASO 3: Generar material de DESARROLLO usando la escala
        # ═══════════════════════════════════════════════════════════════════

        development_notes = []
        current_beat = 0

        # Obtener grados de escala válidos desde el motivo
        # Convertir pitches del motivo a grados de escala
        motif_degrees = []
        for note_info in motif_notes:
            midi = note_info['pitch']
            degree = self.scale_manager.pitch_to_degree(midi)
            if degree is not None:
                motif_degrees.append(degree)

        # Si no hay grados detectados, usar 1-5-3-1 como patrón básico
        if not motif_degrees:
            motif_degrees = [1, 5, 3, 1]

        # Calcular el grado inicial (último del motivo) y octava
        last_midi = last_motif_pitch
        current_degree = self.scale_manager.pitch_to_degree(last_midi)
        if current_degree is None:
            current_degree = 1

        # Determinar octava base (MIDI 60 = C4 = octava 4)
        current_octave = last_midi // 12 - 1

        # Filtrar ritmos para usar solo valores razonables (no 16avos sueltos)
        filtered_rhythms = [r for r in characteristic_rhythms if r >= 0.5]  # mínimo corchea
        if not filtered_rhythms:
            filtered_rhythms = [1.0, 0.5]  # negra y corchea por defecto

        # Tipos de desarrollo basados en libertad
        if variation_freedom == 1:
            # Conservador: repetir grados del motivo, ritmos similares
            dev_patterns = ['echo', 'sequence_up', 'sequence_down']
        elif variation_freedom == 2:
            # Moderado: secuencias, inversiones
            dev_patterns = ['echo', 'sequence_up', 'sequence_down', 'inversion', 'neighbor']
        else:
            # Creativo: más variedad
            dev_patterns = ['echo', 'sequence_up', 'sequence_down', 'inversion',
                          'neighbor', 'leap', 'pedal']

        phrase_position = 0
        notes_in_phrase = 0
        phrase_pattern = random.choice(dev_patterns)

        while current_beat < development_beats:
            # Cambiar patrón cada 4-8 notas
            if notes_in_phrase >= random.randint(4, 8):
                phrase_pattern = random.choice(dev_patterns)
                notes_in_phrase = 0

            # Elegir duración de los ritmos característicos
            duration = random.choice(filtered_rhythms)
            if current_beat + duration > development_beats:
                duration = development_beats - current_beat
                if duration < 0.5:
                    break

            # Elegir siguiente grado basado en el patrón
            if phrase_pattern == 'echo':
                # Eco: repetir grados del motivo
                idx = phrase_position % len(motif_degrees)
                target_degree = motif_degrees[idx]

            elif phrase_pattern == 'sequence_up':
                # Secuencia ascendente: transponer motivo +2 grados
                idx = phrase_position % len(motif_degrees)
                target_degree = motif_degrees[idx] + 2
                if target_degree > 7:
                    target_degree -= 7

            elif phrase_pattern == 'sequence_down':
                # Secuencia descendente: transponer motivo -2 grados
                idx = phrase_position % len(motif_degrees)
                target_degree = motif_degrees[idx] - 2
                if target_degree < 1:
                    target_degree += 7

            elif phrase_pattern == 'inversion':
                # Inversión: espejo alrededor del grado 4
                idx = phrase_position % len(motif_degrees)
                original = motif_degrees[idx]
                target_degree = 8 - original  # Inversión simple
                if target_degree < 1:
                    target_degree = 1
                if target_degree > 7:
                    target_degree = 7

            elif phrase_pattern == 'neighbor':
                # Notas vecinas: grado actual +-1
                step = random.choice([-1, 1])
                target_degree = current_degree + step
                if target_degree < 1:
                    target_degree = 2
                if target_degree > 7:
                    target_degree = 6

            elif phrase_pattern == 'leap':
                # Salto: ir a grados estructurales (1, 3, 5)
                target_degree = random.choice([1, 3, 5])

            elif phrase_pattern == 'pedal':
                # Pedal: alternar entre tónica y otro grado
                if phrase_position % 2 == 0:
                    target_degree = 1
                else:
                    target_degree = random.choice([3, 5])

            else:
                target_degree = current_degree

            # Convertir grado a pitch usando scale_manager
            pitch_name = self.scale_manager.get_pitch_by_degree(target_degree, current_octave)

            # Convertir pitch name (e.g., "eb4", "ab4") a formato LilyPond (e.g., "es'", "aes'")
            lily_pitch = self._pitch_name_to_lilypond(pitch_name)

            # Verificar rango usando music21 para obtener MIDI
            from music21 import pitch as m21pitch
            try:
                m21_pitch = m21pitch.Pitch(pitch_name)
                target_midi = m21_pitch.midi

                # Ajustar octava si está fuera del rango
                while target_midi > motif_max_pitch + 5:
                    target_midi -= 12
                    current_octave -= 1
                    pitch_name = self.scale_manager.get_pitch_by_degree(target_degree, current_octave)
                    lily_pitch = self._pitch_name_to_lilypond(pitch_name)
                while target_midi < motif_min_pitch - 5:
                    target_midi += 12
                    current_octave += 1
                    pitch_name = self.scale_manager.get_pitch_by_degree(target_degree, current_octave)
                    lily_pitch = self._pitch_name_to_lilypond(pitch_name)
            except Exception:
                pass  # Keep the original pitch_name

            # Crear nota Abjad
            try:
                dur_str = self._duration_to_lilypond(duration)
                note = abjad.Note(f"{lily_pitch}{dur_str}")
                development_notes.append(note)
            except Exception:
                note = abjad.Note("c'4")
                development_notes.append(note)
                duration = 1.0

            current_degree = target_degree
            current_beat += duration
            phrase_position += 1
            notes_in_phrase += 1

        # ═══════════════════════════════════════════════════════════════════
        # PASO 4: Crear Staff de desarrollo para formateo
        # ═══════════════════════════════════════════════════════════════════

        development_staff = abjad.Staff(development_notes)

        # ═══════════════════════════════════════════════════════════════════
        # PASO 5: Formatear LilyPond final = Original + Desarrollo
        # ═══════════════════════════════════════════════════════════════════

        lilypond_code = self._format_motif_with_development(
            original_lilypond=original_lilypond,
            development_staff=development_staff,
            title=title,
            composer=composer,
            add_bass=add_bass,
            num_measures=num_measures,
        )

        # Para el Staff de retorno, parseamos todo combinado
        # Pero el LilyPond es lo importante (preserva el original)
        combined_notes = []

        # Parsear original para el staff (solo para retorno)
        parsed_original = self._parse_lilypond_motif(original_lilypond)
        for note_data in parsed_original:
            try:
                note = abjad.Note(f"{note_data['pitch']}{note_data['duration']}")
                combined_notes.append(note)
            except Exception:
                continue

        # Agregar desarrollo - crear nuevas notas para evitar problema de parent
        for leaf in abjad.iterate.leaves(development_staff):
            if isinstance(leaf, abjad.Note):
                # Create a fresh note with same pitch and duration
                pitch = leaf.written_pitch
                duration = abjad.get.duration(leaf)
                pitch_name = pitch.name if hasattr(pitch, 'name') else str(pitch)
                if callable(pitch_name):
                    pitch_name = pitch_name()
                dur_str = self._duration_to_lilypond(float(duration) * 4)
                try:
                    new_note = abjad.Note(f"{pitch_name}{dur_str}")
                    combined_notes.append(new_note)
                except Exception:
                    combined_notes.append(abjad.Note("c'4"))
            elif isinstance(leaf, abjad.Rest):
                duration = abjad.get.duration(leaf)
                dur_str = self._duration_to_lilypond(float(duration) * 4)
                combined_notes.append(abjad.Rest(f"r{dur_str}"))

        combined_staff = abjad.Staff(combined_notes) if combined_notes else abjad.Staff([abjad.Note("c'4")])

        # Agregar firmas
        if combined_notes:
            time_sig = abjad.TimeSignature(self.meter_tuple)
            abjad.attach(time_sig, combined_staff[0])

            key_sig = self._create_key_signature()
            if key_sig:
                abjad.attach(key_sig, combined_staff[0])

        return combined_staff, lilypond_code

    def _pitch_name_to_lilypond(self, pitch_name: str) -> str:
        """
        Convierte nombre de pitch (e.g., "eb4", "ab5", "c4") a formato LilyPond/Abjad.

        Args:
            pitch_name: Nombre como "eb4", "c#5", "g3"

        Returns:
            Nombre LilyPond como "es'", "cis''", "g"
        """
        import re

        # Separar nombre de nota y octava
        match = re.match(r'([a-gA-G])([#b]*)(\d+)', pitch_name)
        if not match:
            return "c'"  # Default

        note = match.group(1).lower()
        accidental = match.group(2)
        octave = int(match.group(3))

        # Convertir accidental a formato Abjad/LilyPond
        # Abjad uses: es (Eb), as (Ab), bes (Bb), des (Db), ges (Gb)
        # NOTE: Only E and A can use shortened 's' form for flats
        # B-flat is 'bes' NOT 'bs' (which would be B-sharp)
        lily_accidental = ""
        if accidental:
            if "#" in accidental:
                lily_accidental = "s" * accidental.count("#")  # Sharp suffix
            elif "b" in accidental:
                # Only E and A use shortened 's' for flats (es, as)
                # All others including B use 'es' (bes, des, ges, etc.)
                if note in ['e', 'a']:
                    lily_accidental = "s" * accidental.count("b")
                else:
                    lily_accidental = "es" * accidental.count("b")

        # Calcular marcas de octava (c' = C4)
        lily_octave = octave - 3
        if lily_octave > 0:
            octave_marks = "'" * lily_octave
        elif lily_octave < 0:
            octave_marks = "," * abs(lily_octave)
        else:
            octave_marks = ""

        return f"{note}{lily_accidental}{octave_marks}"

    def _midi_to_lilypond_pitch(self, midi_number: int, use_english: bool = True) -> str:
        """
        Convierte número MIDI a nombre de nota LilyPond.

        Args:
            midi_number: Número MIDI (60 = C4)
            use_english: Si True, usa notación inglesa (cs, ds) compatible con Abjad.
                         Si False, usa notación holandesa (cis, dis) estándar LilyPond.

        Returns:
            Nombre de nota LilyPond (e.g., "c'", "g''", "d,")
        """
        if use_english:
            # English notation for Abjad compatibility
            pitch_names = ['c', 'cs', 'd', 'ds', 'e', 'f', 'fs', 'g', 'gs', 'a', 'as', 'b']
        else:
            # Dutch/German notation for standard LilyPond
            pitch_names = ['c', 'cis', 'd', 'dis', 'e', 'f', 'fis', 'g', 'gis', 'a', 'ais', 'b']

        pc = midi_number % 12
        octave = midi_number // 12 - 1  # MIDI octave convention

        name = pitch_names[pc]

        # LilyPond octave: c' = C4 (MIDI 60), c = C3 (MIDI 48)
        lily_octave = octave - 3  # c' is octave 4
        if lily_octave > 0:
            octave_marks = "'" * lily_octave
        elif lily_octave < 0:
            octave_marks = "," * abs(lily_octave)
        else:
            octave_marks = ""

        return f"{name}{octave_marks}"

    def _duration_to_lilypond(self, quarter_length: float) -> str:
        """Convierte quarterLength de music21 a notación LilyPond."""
        # Mapeo de duraciones comunes
        dur_map = {
            4.0: "1",      # whole
            3.0: "2.",     # dotted half
            2.0: "2",      # half
            1.5: "4.",     # dotted quarter
            1.0: "4",      # quarter
            0.75: "8.",    # dotted eighth
            0.5: "8",      # eighth
            0.375: "16.",  # dotted sixteenth
            0.25: "16",    # sixteenth
            0.125: "32",   # thirty-second
        }

        if quarter_length in dur_map:
            return dur_map[quarter_length]

        # Aproximar a la más cercana
        closest = min(dur_map.keys(), key=lambda x: abs(x - quarter_length))
        return dur_map[closest]

    def _format_original_only(
        self,
        original_lilypond: str,
        title: str,
        composer: str,
        add_bass: bool,
        num_measures: int,
    ) -> Tuple[abjad.Staff, str]:
        """Formatea solo el motivo original cuando no hay desarrollo."""
        import re

        # Limpiar el LilyPond original de comandos de encabezado
        clean_ly = original_lilypond.strip()

        # Extraer solo el contenido musical (dentro de llaves si existe)
        brace_match = re.search(r'\{([^}]+)\}', clean_ly)
        if brace_match:
            music_content = brace_match.group(1).strip()
        else:
            music_content = clean_ly

        # Construir LilyPond completo
        header = ""
        if title or composer:
            header = "\\header {\n"
            if title:
                header += f'  title = "{title}"\n'
            if composer:
                header += f'  composer = "{composer}"\n'
            header += "}\n\n"

        # Use LilyPondFormatter's mode mapping to get valid LilyPond mode
        mode_command = self.lilypond_formatter._get_lilypond_mode_command()
        key_str = f"\\key {self.key_name.lower()} {mode_command}"
        time_str = f"\\time {self.meter_tuple[0]}/{self.meter_tuple[1]}"

        lilypond_code = f"""\\version "2.24.0"

{header}\\relative c' {{
  {time_str}
  {key_str}
  {music_content}
  \\bar "|."
}}
"""

        # Crear staff para retorno
        parsed = self._parse_lilypond_motif(original_lilypond)
        notes = []
        for note_data in parsed:
            try:
                note = abjad.Note(f"{note_data['pitch']}{note_data['duration']}")
                notes.append(note)
            except Exception:
                continue

        staff = abjad.Staff(notes) if notes else abjad.Staff([abjad.Note("c'4")])

        return staff, lilypond_code

    def _format_motif_with_development(
        self,
        original_lilypond: str,
        development_staff: abjad.Staff,
        title: str,
        composer: str,
        add_bass: bool,
        num_measures: int,
    ) -> str:
        """
        Formatea el LilyPond final combinando original + desarrollo.

        CRÍTICO: El original_lilypond se preserva EXACTAMENTE como el usuario
        lo escribió, incluyendo articulaciones, dinámicas, ligaduras, etc.
        """
        import re

        # ═══════════════════════════════════════════════════════════════════
        # EXTRAER CONTENIDO MUSICAL DEL ORIGINAL
        # ═══════════════════════════════════════════════════════════════════

        clean_ly = original_lilypond.strip()

        # Buscar contenido dentro de llaves
        brace_match = re.search(r'\{([^}]+)\}', clean_ly, re.DOTALL)
        if brace_match:
            original_content = brace_match.group(1).strip()
        else:
            original_content = clean_ly

        # Remover comandos de encabezado del contenido pero PRESERVAR todo lo demás
        # Solo removemos \time, \key, \clef del contenido (se agregan en el wrapper)
        # PERO preservamos articulaciones, dinámicas, ligaduras, etc.

        # Extraer y remover \time
        time_match = re.search(r'\\time\s+(\d+)/(\d+)', original_content)
        if time_match:
            # Usar el time signature del original si existe
            pass  # Ya tenemos self.meter_tuple

        # Remover solo los comandos de setup, preservando todo lo musical
        setup_commands = [
            r'\\time\s+\d+/\d+',
            r'\\key\s+[a-g](?:is|es)?\s*\\(?:major|minor|dorian|phrygian|lydian|mixolydian|locrian)',
            r'\\clef\s+(?:"[^"]*"|[a-z]+)',
            r'\\set\s+\w+\s*=\s*#[^\s]+',
        ]

        music_content = original_content
        for pattern in setup_commands:
            music_content = re.sub(pattern, '', music_content, flags=re.IGNORECASE)

        # Limpiar espacios extra pero preservar estructura
        music_content = re.sub(r'\n\s*\n', '\n', music_content)
        music_content = music_content.strip()

        # Remover \bar "|." final si existe (lo agregamos al final del desarrollo)
        music_content = re.sub(r'\\bar\s*"\|\."\s*$', '', music_content)
        music_content = music_content.strip()

        # ═══════════════════════════════════════════════════════════════════
        # FORMATEAR DESARROLLO
        # ═══════════════════════════════════════════════════════════════════

        development_notes_str = ""
        for leaf in abjad.iterate.leaves(development_staff):
            if isinstance(leaf, abjad.Note):
                # Use abjad.get.duration() for reliable duration extraction
                duration = abjad.get.duration(leaf)

                # Get pitch name directly from Abjad (preserves enharmonic spelling)
                # abjad.lilypond(leaf) gives us the full note with duration
                lily_full = abjad.lilypond(leaf)
                # Extract just the pitch part (before duration number)
                import re
                pitch_match = re.match(r"([a-g][fisesc]*[',-]*)", lily_full)
                if pitch_match:
                    pitch_name = pitch_match.group(1)
                else:
                    pitch_name = "c'"

                # Convertir duración (abjad.Duration to quarterLength)
                dur_str = self._duration_to_lilypond(float(duration) * 4)

                development_notes_str += f"{pitch_name}{dur_str} "

            elif isinstance(leaf, abjad.Rest):
                duration = abjad.get.duration(leaf)
                dur_str = self._duration_to_lilypond(float(duration) * 4)
                development_notes_str += f"r{dur_str} "

        development_notes_str = development_notes_str.strip()

        # ═══════════════════════════════════════════════════════════════════
        # CONSTRUIR LILYPOND FINAL
        # ═══════════════════════════════════════════════════════════════════

        header = ""
        if title or composer:
            header = "\\header {\n"
            if title:
                header += f'  title = "{title}"\n'
            if composer:
                header += f'  composer = "{composer}"\n'
            header += "}\n\n"

        # Use LilyPondFormatter's mode mapping to get valid LilyPond mode
        mode_command = self.lilypond_formatter._get_lilypond_mode_command()
        key_str = f"\\key {self.key_name.lower()} {mode_command}"
        time_str = f"\\time {self.meter_tuple[0]}/{self.meter_tuple[1]}"

        # Combinar: setup + original (con articulaciones) + desarrollo + barra final
        lilypond_code = f"""\\version "2.24.0"

{header}\\relative c' {{
  {time_str}
  {key_str}
  \\clef "treble"

  % === MOTIVO ORIGINAL (preservado literalmente) ===
  {music_content}

  % === DESARROLLO ===
  {development_notes_str}

  \\bar "|."
}}
"""

        return lilypond_code

    def _parse_lilypond_motif(self, lilypond_str: str) -> List[dict]:
        """
        Parsea una cadena de notación LilyPond a una lista de notas.

        Handles the extended format:
        { \\time 4/4 \\key c \\minor \\clef "treble" g'4 c''4 ees''4 d''4 | c''2 b'4 c''4 }

        Args:
            lilypond_str: Notación como "c'4 d' e'8 f'" o formato extendido con comandos

        Returns:
            Lista de dicts con pitch y duration
        """
        import re

        # Clean input
        lilypond_str = lilypond_str.strip()

        # Remove braces
        lilypond_str = re.sub(r'[{}]', ' ', lilypond_str)

        # Remove \key command with its arguments (e.g., \key c \minor, \key d \major)
        # This must come before general command removal
        lilypond_str = re.sub(r'\\key\s+[a-g](?:is|es)?\s*\\(?:major|minor|dorian|phrygian|lydian|mixolydian|locrian)', ' ', lilypond_str, flags=re.IGNORECASE)

        # Remove \clef command with argument (e.g., \clef "treble", \clef bass)
        lilypond_str = re.sub(r'\\clef\s+(?:"[^"]*"|[a-z]+)', ' ', lilypond_str, flags=re.IGNORECASE)

        # Remove \time command with fraction (e.g., \time 4/4)
        lilypond_str = re.sub(r'\\time\s+\d+/\d+', ' ', lilypond_str)

        # Remove remaining LilyPond commands (anything starting with backslash)
        lilypond_str = re.sub(r'\\[a-zA-Z]+', ' ', lilypond_str)

        # Remove quoted strings (any remaining)
        lilypond_str = re.sub(r'"[^"]*"', ' ', lilypond_str)

        # Remove standalone fractions (like 4/4, 3/4 if any remain)
        lilypond_str = re.sub(r'\b\d+/\d+\b', ' ', lilypond_str)

        # Remove bar lines
        lilypond_str = re.sub(r'\|', ' ', lilypond_str)

        # Normalize spaces
        lilypond_str = re.sub(r'\s+', ' ', lilypond_str)

        # Pattern for LilyPond notes:
        # pitch: a-g with optional is/es (sharps/flats) and octave marks (',,)
        # duration: optional number (1,2,4,8,16,32) with optional dots
        # Added word boundary \b at start to avoid matching inside words
        note_pattern = r"\b([a-g](?:is|es|isis|eses)?[',]*)([\d]*\.?)"

        notes = []
        last_duration = "4"  # Default quarter note

        for match in re.finditer(note_pattern, lilypond_str, re.IGNORECASE):
            pitch = match.group(1).lower()
            duration = match.group(2) if match.group(2) else last_duration

            if duration:
                last_duration = duration

            notes.append({
                "pitch": pitch,
                "duration": duration,
            })

        return notes

    def _analyze_motif_key(self, notes: List[dict]) -> Tuple[str, str]:
        """
        Analiza las notas para detectar la tonalidad probable.

        Usa heurísticas simples:
        - Primera/última nota como posible tónica
        - Frecuencia de notas

        Args:
            notes: Lista de dicts con pitch info

        Returns:
            Tuple[key_name, mode]: Tonalidad detectada
        """
        if not notes:
            return "C", "major"

        # Extract pitch classes (without octave)
        import re
        pitch_classes = []
        for note in notes:
            pitch = note["pitch"]
            # Remove octave marks
            pitch_class = re.sub(r"[',]+", "", pitch)
            pitch_classes.append(pitch_class)

        # Count occurrences
        from collections import Counter
        counts = Counter(pitch_classes)

        # First and last notes are often important
        first_note = pitch_classes[0] if pitch_classes else "c"
        last_note = pitch_classes[-1] if pitch_classes else "c"

        # Use first note as potential tonic
        # Map LilyPond pitch to key name
        pitch_to_key = {
            "c": "C", "cis": "C#", "ces": "Cb",
            "d": "D", "dis": "D#", "des": "Db",
            "e": "E", "eis": "E#", "ees": "Eb",
            "f": "F", "fis": "F#", "fes": "Fb",
            "g": "G", "gis": "G#", "ges": "Gb",
            "a": "A", "ais": "A#", "aes": "Ab",
            "b": "B", "bis": "B#", "bes": "Bb",
        }

        detected_key = pitch_to_key.get(first_note, "C")

        # Simple mode detection: check for minor third
        # If we find a minor 3rd from tonic, assume minor
        mode = "major"

        # Get semitones from tonic
        pitch_semitones = {
            "c": 0, "cis": 1, "des": 1, "d": 2, "dis": 3, "ees": 3,
            "e": 4, "fes": 4, "eis": 5, "f": 5, "fis": 6, "ges": 6,
            "g": 7, "gis": 8, "aes": 8, "a": 9, "ais": 10, "bes": 10,
            "b": 11, "ces": 11, "bis": 0,
        }

        tonic_semitone = pitch_semitones.get(first_note, 0)

        for pc in pitch_classes:
            pc_semitone = pitch_semitones.get(pc, 0)
            interval = (pc_semitone - tonic_semitone) % 12
            if interval == 3:  # Minor third
                mode = "minor"
                break

        return detected_key, mode

    def _apply_motif_variation(
        self,
        notes: List[abjad.Note],
        variation_type: str,
        iteration: int,
    ) -> List[abjad.Note]:
        """
        Aplica una variación al motivo original.

        Args:
            notes: Lista de notas originales
            variation_type: Tipo de variación a aplicar
            iteration: Número de iteración (para transposición)

        Returns:
            Lista de nuevas notas variadas
        """
        import random
        import copy

        def get_pitch(note):
            """Get pitch from note, handling callable."""
            pitch = note.written_pitch
            if callable(pitch):
                pitch = pitch()
            return pitch

        def get_pitch_name(note):
            """Get pitch name string from note."""
            pitch = get_pitch(note)
            name = pitch.name
            if callable(name):
                name = name()
            return name

        def get_pitch_number(pitch):
            """Get pitch number from pitch object, handling callable."""
            number = pitch.number
            if callable(number):
                number = number()
            return number

        def get_duration(note):
            """Get duration from note, handling callable."""
            dur = note.written_duration
            if callable(dur):
                dur = dur()
            return dur

        def duration_to_string(dur: abjad.Duration) -> str:
            """Convert duration to LilyPond string."""
            # Common durations: 1=whole, 2=half, 4=quarter, 8=eighth, 16=sixteenth
            dur_map = {
                (1, 1): "1",
                (1, 2): "2",
                (1, 4): "4",
                (1, 8): "8",
                (1, 16): "16",
                (1, 32): "32",
                (3, 8): "4.",  # dotted quarter
                (3, 4): "2.",  # dotted half
                (3, 16): "8.",  # dotted eighth
            }
            key = (dur.numerator, dur.denominator)
            if key in dur_map:
                return dur_map[key]
            # Default: try to find closest
            if dur.numerator == 1:
                return str(dur.denominator)
            return "4"  # Default to quarter

        def create_note(pitch_num: int, duration: abjad.Duration) -> abjad.Note:
            """Create a note from pitch number and duration."""
            pitch = abjad.NamedPitch(pitch_num)
            pitch_name = pitch.name
            if callable(pitch_name):
                pitch_name = pitch_name()
            dur_str = duration_to_string(duration)
            note_str = f"{pitch_name}{dur_str}"
            return abjad.Note(note_str)

        def copy_with_new_duration(note, new_dur) -> abjad.Note:
            """Copy note with new duration."""
            pitch_name = get_pitch_name(note)
            dur_str = duration_to_string(new_dur)
            note_str = f"{pitch_name}{dur_str}"
            return abjad.Note(note_str)

        result = []

        if variation_type == "RHYTHMIC_AUGMENTATION":
            # Double durations
            for note in notes:
                dur = abjad.get.duration(note)
                new_dur = abjad.Duration(dur.numerator * 2, dur.denominator)
                # Limit to whole note max
                if new_dur > abjad.Duration(1, 1):
                    new_dur = abjad.Duration(1, 1)
                result.append(copy_with_new_duration(note, new_dur))

        elif variation_type == "RHYTHMIC_DIMINUTION":
            # Halve durations
            for note in notes:
                dur = abjad.get.duration(note)
                new_dur = abjad.Duration(dur.numerator, dur.denominator * 2)
                # Limit to 16th note min
                if new_dur < abjad.Duration(1, 16):
                    new_dur = abjad.Duration(1, 16)
                result.append(copy_with_new_duration(note, new_dur))

        elif variation_type == "TRANSPOSITION":
            # Transpose by 2nds, 3rds, or 5ths
            intervals = [2, 3, 4, 5, 7]  # In semitones
            interval = random.choice(intervals) * (1 if iteration % 2 == 0 else -1)
            for note in notes:
                pitch = get_pitch(note)
                dur = get_duration(note)
                new_pitch_num = get_pitch_number(pitch) + interval
                # Keep within reasonable range
                while new_pitch_num > 12:
                    new_pitch_num -= 12
                while new_pitch_num < -12:
                    new_pitch_num += 12
                result.append(create_note(new_pitch_num, dur))

        elif variation_type == "MELODIC_INVERSION":
            # Invert intervals around first note
            if notes:
                first_pitch = get_pitch(notes[0])
                first_pitch_num = get_pitch_number(first_pitch)
                for note in notes:
                    pitch = get_pitch(note)
                    dur = get_duration(note)
                    interval = get_pitch_number(pitch) - first_pitch_num
                    new_pitch_num = first_pitch_num - interval
                    result.append(create_note(new_pitch_num, dur))

        elif variation_type == "RETROGRADE":
            # Reverse order
            for note in reversed(notes):
                result.append(copy.deepcopy(note))

        elif variation_type == "INTERVALIC_EXPANSION":
            # Expand intervals
            if len(notes) >= 2:
                result.append(copy.deepcopy(notes[0]))
                last_pitch_num = get_pitch_number(get_pitch(notes[0]))
                for i in range(1, len(notes)):
                    prev_pitch = get_pitch(notes[i-1])
                    curr_pitch = get_pitch(notes[i])
                    dur = get_duration(notes[i])
                    interval = get_pitch_number(curr_pitch) - get_pitch_number(prev_pitch)
                    # Expand interval by ~1.5x
                    new_interval = int(interval * 1.5) if interval != 0 else interval
                    new_pitch_num = last_pitch_num + new_interval
                    result.append(create_note(new_pitch_num, dur))
                    last_pitch_num = new_pitch_num

        elif variation_type == "INTERVALIC_CONTRACTION":
            # Contract intervals
            if len(notes) >= 2:
                result.append(copy.deepcopy(notes[0]))
                last_pitch_num = get_pitch_number(get_pitch(notes[0]))
                for i in range(1, len(notes)):
                    prev_pitch = get_pitch(notes[i-1])
                    curr_pitch = get_pitch(notes[i])
                    dur = get_duration(notes[i])
                    interval = get_pitch_number(curr_pitch) - get_pitch_number(prev_pitch)
                    # Contract interval by ~0.5x
                    new_interval = int(interval * 0.5) if abs(interval) > 1 else interval
                    new_pitch_num = last_pitch_num + new_interval
                    result.append(create_note(new_pitch_num, dur))
                    last_pitch_num = new_pitch_num

        else:
            # Default: return copy
            for note in notes:
                result.append(copy.deepcopy(note))

        return result

    def _create_key_signature(self) -> Optional[abjad.KeySignature]:
        """Crea una firma de clave para el staff."""
        try:
            pitch_class = abjad.NamedPitchClass(self.key_name.lower())
            mode_obj = abjad.Mode(self.mode)
            return abjad.KeySignature(pitch_class, mode_obj)
        except Exception:
            return None

    def _create_simple_harmonic_plan(self, num_measures: int) -> List[HarmonicFunction]:
        """
        Crea un plan armónico simple para el bajo.

        Args:
            num_measures: Número de compases

        Returns:
            Lista de HarmonicFunction para el bajo
        """
        plan = []
        progression = [1, 4, 5, 1]  # I-IV-V-I básico

        # Map degrees to chord qualities
        quality_map = {
            1: "major",
            2: "minor",
            3: "minor",
            4: "major",
            5: "major",
            6: "minor",
            7: "diminished",
        }

        # Map degrees to tension levels
        tension_map = {
            1: 0.0,  # Tonic - rest
            4: 0.3,  # Subdominant - moderate
            5: 0.7,  # Dominant - high tension
        }

        for i in range(num_measures):
            degree = progression[i % len(progression)]
            chord_tones = self.harmony_manager.get_chord_tones_for_function(degree)

            plan.append(HarmonicFunction(
                degree=degree,
                quality=quality_map.get(degree, "major"),
                tension=tension_map.get(degree, 0.3),
                chord_tones=chord_tones,
            ))

        return plan
