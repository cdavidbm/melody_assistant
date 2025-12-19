"""
Aplicador de expresiones musicales.

Centraliza la inicialización y aplicación de:
- Ornamentación
- Dinámicas
- Articulaciones
- Cadencias
- Formas musicales
- Modulación
- Desarrollo motívico
- Secuencias
"""

from typing import Optional, List

import abjad

from .config import ExpressionConfig
from .ornamentation import (
    OrnamentGenerator,
    OrnamentConfig,
    OrnamentStyle,
    apply_ornaments_to_staff,
)
from .dynamics import (
    DynamicGenerator,
    DynamicLevel,
    apply_dynamics_to_staff,
)
from .articulation import (
    ArticulationGenerator,
    apply_articulations_to_staff,
)
from .cadences import CadenceGenerator, CadenceType
from .forms import FormGenerator
from .modulation import ModulationGenerator
from .development import MotivicDeveloper
from .sequences import SequenceGenerator


class ExpressionApplicator:
    """
    Aplica características expresivas a melodías generadas.

    Encapsula la lógica de inicialización y aplicación de todos
    los generadores de expresión musical, separando esta responsabilidad
    del MelodicArchitect principal.
    """

    def __init__(
        self,
        config: ExpressionConfig,
        key_name: str,
        mode: str,
        num_measures: int,
        scale_pitches: Optional[List[str]] = None,
    ):
        """
        Inicializa el aplicador de expresiones.

        Args:
            config: Configuración de expresión
            key_name: Tonalidad base
            mode: Modo musical
            num_measures: Número de compases
            scale_pitches: Tonos de la escala (para ornamentos)
        """
        self.config = config
        self.key_name = key_name
        self.mode = mode
        self.num_measures = num_measures

        # Inicializar generadores
        self._init_generators(scale_pitches or [])

    def _init_generators(self, scale_pitches: List[str]) -> None:
        """Inicializa todos los generadores de expresión."""
        exp = self.config

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
                scale_pitches=scale_pitches,
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

    def apply(self, staff: abjad.Staff) -> abjad.Staff:
        """
        Aplica características expresivas a un staff.

        Args:
            staff: Staff de Abjad con la melodía

        Returns:
            Staff con dinámicas, articulaciones y ornamentos aplicados
        """
        exp = self.config

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
            self._apply_articulations(staff)

        return staff

    def _apply_articulations(self, staff: abjad.Staff) -> None:
        """Aplica articulaciones al staff."""
        # Extraer información de notas
        leaves = list(abjad.select.leaves(staff))
        notes = [leaf for leaf in leaves if isinstance(leaf, abjad.Note)]

        if not notes:
            return

        pitches = [str(n.written_pitch()) for n in notes]
        durations = []
        for n in notes:
            dur = n.written_duration()
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
