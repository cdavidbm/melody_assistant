"""
Configuración centralizada para el generador de melodías.
Agrupa parámetros relacionados en dataclasses para mejor organización.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .models import ImpulseType


@dataclass
class TonalConfig:
    """Configuración de tonalidad y modo."""

    key_name: str = "C"
    mode: str = "major"


@dataclass
class MeterConfig:
    """Configuración de métrica y compás."""

    meter_tuple: Tuple[int, int] = (4, 4)
    subdivisions: Optional[List[int]] = None
    num_measures: int = 8

    def __post_init__(self):
        if self.subdivisions is None:
            self.subdivisions = [self.meter_tuple[0]]


@dataclass
class RhythmConfig:
    """Configuración de patrones rítmicos."""

    complexity: int = 3
    use_rests: bool = True
    rest_probability: float = 0.15


@dataclass
class MelodyConfig:
    """Configuración de generación melódica."""

    impulse_type: ImpulseType = ImpulseType.TETIC
    climax_position: float = 0.75
    climax_intensity: float = 1.5
    max_interval: int = 6
    infraction_rate: float = 0.1
    use_tenoris: bool = False
    tenoris_probability: float = 0.2


@dataclass
class MotifConfig:
    """Configuración de motivos y variaciones."""

    use_motivic_variations: bool = True
    variation_probability: float = 0.4
    variation_freedom: int = 2  # 1=estricta, 2=moderada, 3=libre


@dataclass
class MarkovConfig:
    """Configuración de cadenas de Markov."""

    enabled: bool = False
    composer: str = "bach"  # "bach", "mozart", "beethoven", "combined"
    weight: float = 0.3  # 0.0-1.0 (reducido de 0.5 para evitar atonalidad)
    order: int = 2  # 1-3

    def __post_init__(self):
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"weight debe estar entre 0.0 y 1.0, recibido: {self.weight}")
        if not 1 <= self.order <= 3:
            raise ValueError(f"order debe estar entre 1 y 3, recibido: {self.order}")
        valid_composers = {"bach", "mozart", "beethoven", "combined"}
        if self.composer not in valid_composers:
            raise ValueError(f"composer debe ser uno de {valid_composers}")


@dataclass
class ValidationConfig:
    """Configuración de validación musical."""

    tolerance: float = 0.65  # Umbral de aceptación
    strict_meter: bool = False
    validate_key: bool = True
    validate_range: bool = True


@dataclass
class OutputConfig:
    """Configuración de salida."""

    title: str = "Melodía Generada"
    composer: str = "MelodicArchitect AI"
    auto_save: bool = True
    output_dir: str = "output"


@dataclass
class ExpressionConfig:
    """Configuración de características expresivas."""

    # Ornamentación
    use_ornamentation: bool = False
    ornamentation_style: str = "classical"  # baroque, classical, romantic, minimal

    # Dinámicas
    use_dynamics: bool = True
    base_dynamic: str = "mf"
    climax_dynamic: str = "f"

    # Articulaciones
    use_articulations: bool = True
    articulation_style: str = "classical"

    # Forma
    use_form: bool = False
    form_type: str = "binary"  # binary, ternary, rondo, theme_var

    # Secuencias
    use_sequences: bool = False

    # Desarrollo motívico
    use_development: bool = False
    development_intensity: int = 2  # 1-3

    def __post_init__(self):
        valid_orn_styles = {"baroque", "classical", "romantic", "minimal"}
        if self.ornamentation_style not in valid_orn_styles:
            raise ValueError(f"ornamentation_style debe ser uno de {valid_orn_styles}")

        valid_dynamics = {"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"}
        if self.base_dynamic not in valid_dynamics:
            raise ValueError(f"base_dynamic debe ser uno de {valid_dynamics}")
        if self.climax_dynamic not in valid_dynamics:
            raise ValueError(f"climax_dynamic debe ser uno de {valid_dynamics}")

        valid_art_styles = {"baroque", "classical", "romantic"}
        if self.articulation_style not in valid_art_styles:
            raise ValueError(f"articulation_style debe ser uno de {valid_art_styles}")

        valid_forms = {"binary", "ternary", "rondo", "theme_var"}
        if self.form_type not in valid_forms:
            raise ValueError(f"form_type debe ser uno de {valid_forms}")

        if not 1 <= self.development_intensity <= 3:
            raise ValueError(f"development_intensity debe estar entre 1 y 3")


@dataclass
class GenerationConfig:
    """
    Configuración completa para la generación de melodías.

    Agrupa todas las sub-configuraciones en un solo objeto.
    """

    tonal: TonalConfig = field(default_factory=TonalConfig)
    meter: MeterConfig = field(default_factory=MeterConfig)
    rhythm: RhythmConfig = field(default_factory=RhythmConfig)
    melody: MelodyConfig = field(default_factory=MelodyConfig)
    motif: MotifConfig = field(default_factory=MotifConfig)
    markov: MarkovConfig = field(default_factory=MarkovConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def from_simple_params(
        cls,
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
    ) -> "GenerationConfig":
        """
        Crea una configuración desde parámetros simples.

        Proporciona compatibilidad con la API original de MelodicArchitect.
        """
        return cls(
            tonal=TonalConfig(key_name=key_name, mode=mode),
            meter=MeterConfig(
                meter_tuple=meter_tuple,
                subdivisions=subdivisions,
                num_measures=num_measures,
            ),
            rhythm=RhythmConfig(
                complexity=rhythmic_complexity,
                use_rests=use_rests,
                rest_probability=rest_probability,
            ),
            melody=MelodyConfig(
                impulse_type=impulse_type,
                climax_position=climax_position,
                climax_intensity=climax_intensity,
                max_interval=max_interval,
                infraction_rate=infraction_rate,
                use_tenoris=use_tenoris,
                tenoris_probability=tenoris_probability,
            ),
            motif=MotifConfig(
                use_motivic_variations=use_motivic_variations,
                variation_probability=variation_probability,
                variation_freedom=variation_freedom,
            ),
            markov=MarkovConfig(
                enabled=use_markov,
                composer=markov_composer,
                weight=markov_weight,
                order=markov_order,
            ),
        )
