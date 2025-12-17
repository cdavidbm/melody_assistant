"""
Clase principal MelodicArchitect.
Orquesta todos los módulos para la generación de melodías.
"""

from typing import Tuple, Optional, List

import abjad

from .models import ImpulseType, MelodicContour
from .scales import ScaleManager
from .harmony import HarmonyManager
from .rhythm import RhythmGenerator
from .pitch import PitchSelector
from .motif import MotifGenerator
from .lilypond import LilyPondFormatter
from .generation import PeriodGenerator


class MelodicArchitect:
    """
    Arquitecto melódico basado en teoría musical clásica.

    Implementa el algoritmo "Symmetry & Logic" en tres capas:
    I. Configuración de la Realidad Musical
    II. Generación del ADN (Motivo y Frase)
    III. Desarrollo y Cierre (Período y Cadencia)
    """

    def __init__(
        self,
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
    ):
        """
        Inicializa el arquitecto melódico.

        Args:
            key_name: Nombre de la tonalidad (ej: "C", "D", "Eb")
            mode: Modo musical (uno de los 21 soportados)
            meter_tuple: Compás (numerador, denominador)
            subdivisions: Para métricas amalgama, subdivisión de pulsos
            num_measures: Número de compases del período
            impulse_type: Tipo de impulso inicial
            infraction_rate: Tasa de infracción (0.0-1.0)
            rhythmic_complexity: Complejidad rítmica (1-5)
            use_rests: Si se deben usar silencios como respiraciones
            rest_probability: Probabilidad de usar silencio
            use_motivic_variations: Si se deben aplicar variaciones motívicas
            variation_probability: Probabilidad de aplicar variación
            climax_position: Posición del clímax melódico (0.0-1.0)
            climax_intensity: Intensidad del clímax (multiplicador de registro)
            max_interval: Máximo salto permitido (default: 6 = sexta)
            use_tenoris: Usar quinta como nota sostenedora
            tenoris_probability: Probabilidad de tenoris
            variation_freedom: Libertad de variación (1=estricta, 2=moderada, 3=libre)
        """
        self.key_name = key_name
        self.mode = mode
        self.meter_tuple = meter_tuple
        self.subdivisions = subdivisions or [meter_tuple[0]]
        self.num_measures = num_measures
        self.impulse_type = impulse_type

        # Crear contorno melódico
        self.contour = MelodicContour(
            climax_position=climax_position,
            climax_emphasis=climax_intensity,
        )

        # Inicializar componentes
        self.scale_manager = ScaleManager(key_name, mode)

        self.rhythm_generator = RhythmGenerator(
            meter_tuple=meter_tuple,
            subdivisions=self.subdivisions,
            rhythmic_complexity=rhythmic_complexity,
            num_measures=num_measures,
        )

        self.harmony_manager = HarmonyManager(
            mode=mode,
            num_measures=num_measures,
            strong_beats=self.rhythm_generator.strong_beats,
        )

        self.pitch_selector = PitchSelector(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            contour=self.contour,
            num_measures=num_measures,
            max_interval=max_interval,
            use_tenoris=use_tenoris,
            tenoris_probability=tenoris_probability,
            infraction_rate=infraction_rate,
            use_rests=use_rests,
            rest_probability=rest_probability,
            impulse_type=impulse_type,
            meter_tuple=meter_tuple,
        )

        climax_measure = int(num_measures * climax_position)
        self.motif_generator = MotifGenerator(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            rhythmic_complexity=rhythmic_complexity,
            variation_freedom=variation_freedom,
            use_motivic_variations=use_motivic_variations,
            variation_probability=variation_probability,
            contour=self.contour,
            climax_measure=climax_measure,
        )

        self.lilypond_formatter = LilyPondFormatter(
            scale_manager=self.scale_manager,
            mode=mode,
            meter_tuple=meter_tuple,
        )

        self.period_generator = PeriodGenerator(
            scale_manager=self.scale_manager,
            harmony_manager=self.harmony_manager,
            rhythm_generator=self.rhythm_generator,
            pitch_selector=self.pitch_selector,
            motif_generator=self.motif_generator,
            lilypond_formatter=self.lilypond_formatter,
            num_measures=num_measures,
            meter_tuple=meter_tuple,
        )

    def generate_period(self) -> abjad.Staff:
        """
        Genera un período musical completo (método tradicional).

        Returns:
            abjad.Staff con la melodía generada
        """
        return self.period_generator.generate_period()

    def generate_period_hierarchical(self) -> abjad.Staff:
        """
        Genera un período musical con jerarquía formal verdadera.

        Returns:
            abjad.Staff con la melodía generada jerárquicamente
        """
        return self.period_generator.generate_period_hierarchical()

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
        return self.lilypond_formatter.format_output(staff, title=title, composer=composer)
