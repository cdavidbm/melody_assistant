"""
Clase principal MelodicArchitect.
Orquesta todos los módulos para la generación de melodías.
"""

from typing import Tuple, Optional, List, Union

import abjad

from .models import ImpulseType, MelodicContour, Period
from .config import GenerationConfig, TonalConfig, MeterConfig, RhythmConfig, MelodyConfig, MotifConfig, MarkovConfig
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
        )

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
