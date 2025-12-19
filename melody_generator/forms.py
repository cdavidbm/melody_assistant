"""
Formas musicales largas.
Implementa estructuras formales: binaria, ternaria, rondó, tema con variaciones.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable
from enum import Enum
import copy


class FormType(Enum):
    """Tipos de forma musical."""
    BINARY = "binary"           # A-B
    ROUNDED_BINARY = "rounded"  # A-B-A'
    TERNARY = "ternary"         # A-B-A
    RONDO = "rondo"             # A-B-A-C-A
    THEME_VARIATIONS = "theme_var"  # A-A1-A2-A3...
    THROUGH_COMPOSED = "through"    # Sin repeticiones


class SectionCharacter(Enum):
    """Carácter de cada sección."""
    STABLE = "stable"           # Tónica, estable
    CONTRASTING = "contrasting" # Tonalidad/carácter diferente
    DEVELOPMENTAL = "developmental"  # Desarrollo motívico
    TRANSITIONAL = "transitional"    # Transición
    CLOSING = "closing"         # Cierre/coda


@dataclass
class FormSection:
    """
    Representa una sección de la forma.

    Cada sección tiene un nombre (A, B, etc.), duración,
    tonalidad y carácter específico.
    """
    name: str                   # "A", "B", "C", "A'", etc.
    num_measures: int           # Duración en compases
    key_name: str              # Tonalidad de la sección
    mode: str                  # Modo
    character: SectionCharacter = SectionCharacter.STABLE
    is_variation: bool = False  # Si es variación de otra sección
    base_section: Optional[str] = None  # Sección base si es variación
    dynamic_start: str = "mf"   # Dinámica inicial
    tempo_change: Optional[str] = None  # Cambio de tempo opcional


@dataclass
class FormPlan:
    """
    Plan formal completo para una pieza.

    Define la estructura macro y proporciona secciones
    configuradas para generación.
    """
    form_type: FormType
    sections: List[FormSection]
    total_measures: int = 0

    def __post_init__(self):
        self.total_measures = sum(s.num_measures for s in self.sections)

    def get_section_at_measure(self, measure: int) -> Optional[FormSection]:
        """Obtiene la sección que contiene un compás específico."""
        current = 0
        for section in self.sections:
            if current <= measure < current + section.num_measures:
                return section
            current += section.num_measures
        return None

    def get_section_boundaries(self) -> List[int]:
        """Retorna los compases donde empiezan nuevas secciones."""
        boundaries = [0]
        current = 0
        for section in self.sections[:-1]:
            current += section.num_measures
            boundaries.append(current)
        return boundaries


class FormGenerator:
    """
    Genera estructuras formales para piezas musicales.

    Las formas definen la estructura macro de la pieza,
    incluyendo repeticiones, contrastes y desarrollos.
    """

    def __init__(
        self,
        base_key: str = "C",
        base_mode: str = "major",
        measures_per_section: int = 8,
    ):
        """
        Inicializa el generador de formas.

        Args:
            base_key: Tonalidad principal
            base_mode: Modo principal
            measures_per_section: Compases por sección (default 8)
        """
        self.base_key = base_key
        self.base_mode = base_mode
        self.measures_per_section = measures_per_section

        # Relaciones tonales comunes
        self.related_keys = self._get_related_keys()

    def _get_related_keys(self) -> Dict[str, str]:
        """
        Obtiene tonalidades relacionadas a la principal.

        Returns:
            Dict con relaciones: dominant, subdominant, relative, parallel
        """
        # Círculo de quintas simplificado
        fifths_major = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
        fifths_minor = ["A", "E", "B", "F#", "C#", "G#", "D#", "Bb", "F", "C", "G", "D"]

        key = self.base_key
        is_major = self.base_mode in ["major", "ionian"]

        try:
            if is_major:
                idx = fifths_major.index(key)
                dominant = fifths_major[(idx + 1) % 12]
                subdominant = fifths_major[(idx - 1) % 12]
                relative = fifths_minor[idx]
                parallel = key  # Para menor paralelo
            else:
                idx = fifths_minor.index(key)
                dominant = fifths_minor[(idx + 1) % 12]
                subdominant = fifths_minor[(idx - 1) % 12]
                relative = fifths_major[idx]
                parallel = key
        except ValueError:
            # Fallback si la tonalidad no está en la lista
            dominant = key
            subdominant = key
            relative = key
            parallel = key

        return {
            "tonic": key,
            "dominant": dominant,
            "subdominant": subdominant,
            "relative": relative,
            "parallel": parallel,
        }

    def create_binary_form(
        self,
        with_repeats: bool = True,
    ) -> FormPlan:
        """
        Crea forma binaria (A-B).

        La sección A establece la tónica, B va a dominante o relativo.
        Común en danzas barrocas y canciones populares.

        Args:
            with_repeats: Si incluir indicaciones de repetición

        Returns:
            FormPlan para forma binaria
        """
        sections = [
            FormSection(
                name="A",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.STABLE,
                dynamic_start="mf",
            ),
            FormSection(
                name="B",
                num_measures=self.measures_per_section,
                key_name=self.related_keys["dominant"],
                mode=self.base_mode,
                character=SectionCharacter.CONTRASTING,
                dynamic_start="f",
            ),
        ]

        return FormPlan(
            form_type=FormType.BINARY,
            sections=sections,
        )

    def create_rounded_binary_form(self) -> FormPlan:
        """
        Crea forma binaria redondeada (A-B-A').

        Similar a binaria pero retorna al material A al final.
        Muy común en el período clásico.

        Returns:
            FormPlan para forma binaria redondeada
        """
        sections = [
            FormSection(
                name="A",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.STABLE,
                dynamic_start="mf",
            ),
            FormSection(
                name="B",
                num_measures=self.measures_per_section,
                key_name=self.related_keys["dominant"],
                mode=self.base_mode,
                character=SectionCharacter.DEVELOPMENTAL,
                dynamic_start="f",
            ),
            FormSection(
                name="A'",
                num_measures=self.measures_per_section // 2,  # A' más corto
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.CLOSING,
                is_variation=True,
                base_section="A",
                dynamic_start="mp",
            ),
        ]

        return FormPlan(
            form_type=FormType.ROUNDED_BINARY,
            sections=sections,
        )

    def create_ternary_form(
        self,
        contrasting_mode: str = None,
    ) -> FormPlan:
        """
        Crea forma ternaria (A-B-A).

        A y A' son similares, B contrasta fuertemente.
        B puede estar en modo menor si A es mayor (o viceversa).

        Args:
            contrasting_mode: Modo para sección B (None = relativo)

        Returns:
            FormPlan para forma ternaria
        """
        # Determinar modo contrastante
        if contrasting_mode is None:
            if self.base_mode in ["major", "ionian"]:
                b_mode = "minor"
                b_key = self.related_keys["relative"]
            else:
                b_mode = "major"
                b_key = self.related_keys["relative"]
        else:
            b_mode = contrasting_mode
            b_key = self.base_key

        sections = [
            FormSection(
                name="A",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.STABLE,
                dynamic_start="mf",
            ),
            FormSection(
                name="B",
                num_measures=self.measures_per_section,
                key_name=b_key,
                mode=b_mode,
                character=SectionCharacter.CONTRASTING,
                dynamic_start="p",  # B suele ser más suave
            ),
            FormSection(
                name="A",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.STABLE,
                dynamic_start="mf",
            ),
        ]

        return FormPlan(
            form_type=FormType.TERNARY,
            sections=sections,
        )

    def create_rondo_form(
        self,
        num_episodes: int = 2,
    ) -> FormPlan:
        """
        Crea forma rondó (A-B-A-C-A...).

        El tema A (ritornello) alterna con episodios contrastantes.
        Muy común en finales de sonatas y conciertos.

        Args:
            num_episodes: Número de episodios (B, C, etc.)

        Returns:
            FormPlan para forma rondó
        """
        sections = []
        episode_keys = [
            self.related_keys["dominant"],
            self.related_keys["subdominant"],
            self.related_keys["relative"],
        ]

        for i in range(num_episodes):
            # Sección A (ritornello)
            sections.append(FormSection(
                name="A",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.STABLE,
                dynamic_start="f" if i == 0 else "mf",
            ))

            # Episodio
            episode_name = chr(ord("B") + i)  # B, C, D...
            sections.append(FormSection(
                name=episode_name,
                num_measures=self.measures_per_section,
                key_name=episode_keys[i % len(episode_keys)],
                mode=self.base_mode,
                character=SectionCharacter.CONTRASTING,
                dynamic_start="mp",
            ))

        # A final
        sections.append(FormSection(
            name="A",
            num_measures=self.measures_per_section,
            key_name=self.base_key,
            mode=self.base_mode,
            character=SectionCharacter.CLOSING,
            dynamic_start="f",
        ))

        return FormPlan(
            form_type=FormType.RONDO,
            sections=sections,
        )

    def create_theme_and_variations(
        self,
        num_variations: int = 4,
        variation_types: List[str] = None,
    ) -> FormPlan:
        """
        Crea tema con variaciones (A-A1-A2-A3...).

        Cada variación mantiene la estructura armónica
        pero transforma el material melódico/rítmico.

        Args:
            num_variations: Número de variaciones
            variation_types: Tipos de variación para cada una

        Returns:
            FormPlan para tema con variaciones
        """
        if variation_types is None:
            variation_types = [
                "rhythmic",      # Variación rítmica
                "ornamental",    # Con ornamentos
                "minor",         # En modo menor
                "virtuosic",     # Virtuosística
            ]

        sections = [
            # Tema
            FormSection(
                name="Tema",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=self.base_mode,
                character=SectionCharacter.STABLE,
                dynamic_start="mf",
            ),
        ]

        for i in range(num_variations):
            var_type = variation_types[i % len(variation_types)]

            # Determinar características según tipo
            if var_type == "minor":
                mode = "minor"
                dynamic = "p"
            elif var_type == "virtuosic":
                mode = self.base_mode
                dynamic = "f"
            else:
                mode = self.base_mode
                dynamic = "mf"

            sections.append(FormSection(
                name=f"Var. {i + 1}",
                num_measures=self.measures_per_section,
                key_name=self.base_key,
                mode=mode,
                character=SectionCharacter.DEVELOPMENTAL,
                is_variation=True,
                base_section="Tema",
                dynamic_start=dynamic,
            ))

        return FormPlan(
            form_type=FormType.THEME_VARIATIONS,
            sections=sections,
        )

    def get_form_description(self, form_type: FormType) -> str:
        """Retorna descripción de una forma."""
        descriptions = {
            FormType.BINARY: "Forma Binaria (A-B): Dos secciones contrastantes",
            FormType.ROUNDED_BINARY: "Binaria Redondeada (A-B-A'): Retorno al material inicial",
            FormType.TERNARY: "Forma Ternaria (A-B-A): Contraste central con recapitulación",
            FormType.RONDO: "Rondó (A-B-A-C-A): Ritornello alternando con episodios",
            FormType.THEME_VARIATIONS: "Tema con Variaciones: Transformaciones del tema",
            FormType.THROUGH_COMPOSED: "Durchkomponiert: Sin repeticiones formales",
        }
        return descriptions.get(form_type, "Forma no especificada")


class FormAnalyzer:
    """
    Analiza estructuras formales en piezas existentes.

    Útil para validar que la forma generada cumple
    con las expectativas formales.
    """

    def __init__(self):
        self.similarity_threshold = 0.7

    def detect_repetitions(
        self,
        sections_data: List[dict],
    ) -> List[Tuple[int, int, float]]:
        """
        Detecta secciones que se repiten.

        Args:
            sections_data: Lista de datos de cada sección
                          (notas, ritmos, armonía)

        Returns:
            Lista de tuplas (idx1, idx2, similarity)
        """
        repetitions = []

        for i, sec1 in enumerate(sections_data):
            for j, sec2 in enumerate(sections_data[i+1:], i+1):
                similarity = self._calculate_similarity(sec1, sec2)
                if similarity >= self.similarity_threshold:
                    repetitions.append((i, j, similarity))

        return repetitions

    def _calculate_similarity(
        self,
        section1: dict,
        section2: dict,
    ) -> float:
        """
        Calcula similaridad entre dos secciones.

        Returns:
            Valor entre 0.0 (diferentes) y 1.0 (idénticas)
        """
        # Comparar notas
        notes1 = section1.get("notes", [])
        notes2 = section2.get("notes", [])

        if not notes1 or not notes2:
            return 0.0

        # Normalizar longitudes
        min_len = min(len(notes1), len(notes2))
        matches = sum(1 for i in range(min_len) if notes1[i] == notes2[i])

        return matches / min_len

    def infer_form_type(
        self,
        sections_data: List[dict],
    ) -> FormType:
        """
        Infiere el tipo de forma basado en repeticiones.

        Args:
            sections_data: Datos de cada sección

        Returns:
            FormType inferido
        """
        num_sections = len(sections_data)
        repetitions = self.detect_repetitions(sections_data)

        if num_sections == 2:
            return FormType.BINARY

        if num_sections == 3:
            # Verificar si primera y última son similares
            for i, j, sim in repetitions:
                if i == 0 and j == 2:
                    return FormType.TERNARY
            return FormType.ROUNDED_BINARY

        if num_sections >= 5:
            # Verificar patrón de rondó (A aparece múltiples veces)
            a_appearances = sum(1 for i, j, _ in repetitions if i == 0)
            if a_appearances >= 2:
                return FormType.RONDO

        return FormType.THROUGH_COMPOSED


def get_section_transition_suggestions(
    from_section: FormSection,
    to_section: FormSection,
) -> dict:
    """
    Sugiere características para la transición entre secciones.

    Args:
        from_section: Sección de origen
        to_section: Sección de destino

    Returns:
        Dict con sugerencias de transición
    """
    suggestions = {
        "use_retransition": False,
        "cadence_type": "half",  # Semicadencia por defecto
        "dynamic_change": None,
        "register_shift": 0,
    }

    # Si hay cambio de tonalidad, usar retransición
    if from_section.key_name != to_section.key_name:
        suggestions["use_retransition"] = True
        suggestions["cadence_type"] = "half"

    # Si volvemos a A, cadencia auténtica
    if to_section.name == "A" and from_section.name != "A":
        suggestions["cadence_type"] = "authentic"

    # Cambios dinámicos
    dynamics_order = ["pp", "p", "mp", "mf", "f", "ff"]
    try:
        from_idx = dynamics_order.index(from_section.dynamic_start)
        to_idx = dynamics_order.index(to_section.dynamic_start)
        if to_idx > from_idx:
            suggestions["dynamic_change"] = "crescendo"
        elif to_idx < from_idx:
            suggestions["dynamic_change"] = "diminuendo"
    except ValueError:
        pass

    return suggestions
