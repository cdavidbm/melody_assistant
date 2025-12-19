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

# Nuevos módulos de expresión musical
from .ornamentation import OrnamentGenerator, OrnamentConfig, OrnamentStyle, apply_ornaments_to_staff
from .dynamics import DynamicGenerator, DynamicLevel, apply_dynamics_to_staff
from .articulation import ArticulationGenerator, apply_articulations_to_staff
from .cadences import CadenceGenerator, CadenceType
from .forms import FormGenerator, FormType, FormPlan
from .modulation import ModulationGenerator
from .development import MotivicDeveloper
from .sequences import SequenceGenerator


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
        markov_weight: float = 0.5,
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

        # Inicializar generadores de expresión
        self._init_expression_generators()

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

    def _init_expression_generators(self):
        """Inicializa los generadores de expresión musical."""
        exp = self.expression_config

        # Generador de ornamentos
        if exp.use_ornamentation:
            style_map = {
                "baroque": OrnamentStyle.BAROQUE,
                "classical": OrnamentStyle.CLASSICAL,
                "romantic": OrnamentStyle.ROMANTIC,
                "minimal": OrnamentStyle.MINIMAL,
            }
            ornament_config = OrnamentConfig(
                style=style_map.get(exp.ornamentation_style, OrnamentStyle.CLASSICAL)
            )
            self.ornament_generator = OrnamentGenerator(
                config=ornament_config,
                scale_pitches=self.scale_manager.get_scale_pitches(),
            )
        else:
            self.ornament_generator = None

        # Generador de dinámicas
        if exp.use_dynamics:
            level_map = {
                "pp": DynamicLevel.PP,
                "p": DynamicLevel.P,
                "mp": DynamicLevel.MP,
                "mf": DynamicLevel.MF,
                "f": DynamicLevel.F,
                "ff": DynamicLevel.FF,
            }
            self.dynamic_generator = DynamicGenerator(
                base_level=level_map.get(exp.base_dynamic, DynamicLevel.MF),
                climax_level=level_map.get(exp.climax_dynamic, DynamicLevel.F),
                style=exp.articulation_style,
            )
        else:
            self.dynamic_generator = None

        # Generador de articulaciones
        if exp.use_articulations:
            self.articulation_generator = ArticulationGenerator(
                style=exp.articulation_style,
            )
        else:
            self.articulation_generator = None

        # Generador de cadencias
        self.cadence_generator = CadenceGenerator(
            mode=self.mode,
            style=exp.articulation_style,
        )

        # Generador de formas
        self.form_generator = FormGenerator(
            base_key=self.key_name,
            base_mode=self.mode,
            measures_per_section=self.num_measures,
        )

        # Generador de modulaciones
        self.modulation_generator = ModulationGenerator(
            source_key=self.key_name,
            source_mode=self.mode,
        )

        # Desarrollador motívico
        self.motivic_developer = MotivicDeveloper(
            intensity_level=exp.development_intensity,
        )

        # Generador de secuencias
        self.sequence_generator = SequenceGenerator()

    def apply_expression(self, staff: abjad.Staff) -> abjad.Staff:
        """
        Aplica características expresivas a un staff generado.

        Args:
            staff: Staff de Abjad con la melodía

        Returns:
            Staff con dinámicas, articulaciones y ornamentos aplicados
        """
        exp = self.expression_config

        # Aplicar ornamentos (primero, antes de otras expresiones)
        if exp.use_ornamentation and self.ornament_generator:
            apply_ornaments_to_staff(
                staff,
                self.ornament_generator,
                num_measures=self.num_measures,
            )

        # Aplicar dinámicas
        if exp.use_dynamics and self.dynamic_generator:
            dynamic_plan = self.dynamic_generator.generate_period_dynamics(
                num_measures=self.num_measures,
                notes_per_measure=4,  # Aproximado
            )
            apply_dynamics_to_staff(staff, dynamic_plan)

        # Aplicar articulaciones
        if exp.use_articulations and self.articulation_generator:
            # Extraer información de notas
            leaves = list(abjad.select.leaves(staff))
            notes = [l for l in leaves if isinstance(l, abjad.Note)]

            if notes:
                pitches = [str(n.written_pitch()) for n in notes]
                durations = []
                for n in notes:
                    dur = n.written_duration()  # Method call with parentheses
                    durations.append((dur.numerator, dur.denominator))

                # Determinar tiempos fuertes (simplificado)
                strong_beats = [i % 4 == 0 for i in range(len(notes))]

                # Determinar cadencias (últimas notas de cada 4 compases)
                is_cadence = [False] * len(notes)
                notes_per_measure = max(1, len(notes) // self.num_measures)
                for i in range(len(notes)):
                    measure_idx = i // notes_per_measure
                    if (measure_idx + 1) % 4 == 0:
                        is_cadence[i] = True

                # Generar articulaciones
                articulations = self.articulation_generator.generate_articulations(
                    pitches=pitches,
                    durations=durations,
                    strong_beats=strong_beats,
                    is_cadence=is_cadence,
                )

                # Generar slurs
                phrase_boundaries = [
                    i * notes_per_measure * 4
                    for i in range(1, self.num_measures // 4 + 1)
                ]
                slurs = self.articulation_generator.generate_slurs(
                    pitches=pitches,
                    phrase_boundaries=phrase_boundaries,
                )

                # Aplicar al staff
                apply_articulations_to_staff(staff, articulations, slurs)

        return staff

    def generate_period_with_expression(self) -> abjad.Staff:
        """
        Genera un período musical con características expresivas aplicadas.

        Returns:
            abjad.Staff con melodía, dinámicas, articulaciones, etc.
        """
        staff = self.generate_period()
        return self.apply_expression(staff)

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

        Args:
            cadence_type: "authentic", "half", "deceptive", "plagal"
            is_final: Si es cadencia final

        Returns:
            Dict con grados melódicos y duraciones
        """
        type_map = {
            "authentic": CadenceType.AUTHENTIC_PERFECT,
            "half": CadenceType.HALF,
            "deceptive": CadenceType.DECEPTIVE,
            "plagal": CadenceType.PLAGAL,
        }
        cad_type = type_map.get(cadence_type, CadenceType.AUTHENTIC_PERFECT)

        if cad_type == CadenceType.AUTHENTIC_PERFECT:
            gesture = self.cadence_generator.get_authentic_cadence(perfect=True)
        elif cad_type == CadenceType.HALF:
            gesture = self.cadence_generator.get_half_cadence()
        elif cad_type == CadenceType.DECEPTIVE:
            gesture = self.cadence_generator.get_deceptive_cadence()
        else:
            gesture = self.cadence_generator.get_plagal_cadence()

        return {
            "melody_degrees": gesture.melody_degrees,
            "durations": gesture.durations,
            "bass_degrees": gesture.bass_degrees,
            "has_trill": gesture.ornament_type == "trill",
        }

    def get_modulation_plan(
        self,
        target_relationship: str = "dominant",
    ) -> dict:
        """
        Obtiene un plan de modulación a una tonalidad relacionada.

        Args:
            target_relationship: "dominant", "relative", "subdominant", "parallel"

        Returns:
            Dict con información de la modulación
        """
        from .modulation import KeyRelationship

        rel_map = {
            "dominant": KeyRelationship.DOMINANT,
            "relative": KeyRelationship.RELATIVE,
            "subdominant": KeyRelationship.SUBDOMINANT,
            "parallel": KeyRelationship.PARALLEL,
        }

        related_keys = self.modulation_generator.get_related_keys()
        relationship = rel_map.get(target_relationship, KeyRelationship.DOMINANT)

        if relationship in related_keys:
            target_key, target_mode = related_keys[relationship]
            plan = self.modulation_generator.create_pivot_modulation(
                target_key, target_mode
            )
            return {
                "source": f"{plan.source_key} {plan.source_mode}",
                "target": f"{plan.target_key} {plan.target_mode}",
                "type": plan.modulation_type.value,
                "pivot_chord": plan.pivot_chord.chord_name if plan.pivot_chord else None,
                "melodic_approach": plan.melodic_degrees_source,
            }

        return {"error": "Relationship not found"}
