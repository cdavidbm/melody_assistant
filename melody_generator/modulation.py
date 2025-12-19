"""
Modulación a tonalidades relacionadas.
Implementa técnicas de modulación: pivote, directa, cromática.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
from enum import Enum


class ModulationType(Enum):
    """Tipos de modulación."""
    PIVOT_CHORD = "pivot"       # Acorde pivote (común a ambas tonalidades)
    DIRECT = "direct"           # Modulación directa (sin preparación)
    CHROMATIC = "chromatic"     # Por alteraciones cromáticas
    SEQUENTIAL = "sequential"   # Durante una secuencia
    ENHARMONIC = "enharmonic"   # Reinterpretación enarmónica


class KeyRelationship(Enum):
    """Relación entre tonalidades."""
    PARALLEL = "parallel"       # Mayor/menor con misma tónica
    RELATIVE = "relative"       # Relativo mayor/menor
    DOMINANT = "dominant"       # Tonalidad de la dominante
    SUBDOMINANT = "subdominant" # Tonalidad de la subdominante
    SUPERTONIC = "supertonic"   # ii de mayor
    MEDIANT = "mediant"         # iii o bIII
    SUBMEDIANT = "submediant"   # vi o bVI


@dataclass
class PivotChord:
    """
    Representa un acorde pivote para modulación.

    El acorde pivote tiene función en ambas tonalidades,
    facilitando una transición suave.
    """
    chord_name: str             # Nombre del acorde (ej: "Am")
    function_in_source: str     # Función en tonalidad origen (ej: "vi")
    function_in_target: str     # Función en tonalidad destino (ej: "ii")
    common_tones: List[str]     # Notas comunes


@dataclass
class ModulationPlan:
    """
    Plan completo para una modulación.

    Define el punto de inicio, el proceso de modulación,
    y la confirmación de la nueva tonalidad.
    """
    source_key: str
    source_mode: str
    target_key: str
    target_mode: str
    modulation_type: ModulationType
    pivot_chord: Optional[PivotChord] = None
    transition_measures: int = 2
    confirmation_cadence: str = "authentic"  # Tipo de cadencia confirmatoria
    melodic_degrees_source: List[int] = None  # Grados en tonalidad origen
    melodic_degrees_target: List[int] = None  # Grados en tonalidad destino


class ModulationGenerator:
    """
    Genera planes de modulación entre tonalidades.

    Las modulaciones añaden variedad tonal y permiten
    crear estructuras formales más elaboradas.
    """

    # Círculo de quintas
    CIRCLE_MAJOR = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
    CIRCLE_MINOR = ["A", "E", "B", "F#", "C#", "G#", "D#", "Bb", "F", "C", "G", "D"]

    # Enarmónicos
    ENHARMONICS = {
        "C#": "Db", "Db": "C#",
        "D#": "Eb", "Eb": "D#",
        "F#": "Gb", "Gb": "F#",
        "G#": "Ab", "Ab": "G#",
        "A#": "Bb", "Bb": "A#",
    }

    def __init__(
        self,
        source_key: str = "C",
        source_mode: str = "major",
    ):
        """
        Inicializa el generador de modulaciones.

        Args:
            source_key: Tonalidad de origen
            source_mode: Modo de origen
        """
        self.source_key = source_key
        self.source_mode = source_mode
        self.is_minor = source_mode in [
            "minor", "harmonic_minor", "melodic_minor",
            "dorian", "phrygian", "aeolian"
        ]

    def get_related_keys(self) -> Dict[KeyRelationship, Tuple[str, str]]:
        """
        Obtiene todas las tonalidades relacionadas a la actual.

        Returns:
            Dict con relación -> (tonalidad, modo)
        """
        related = {}

        try:
            if self.is_minor:
                idx = self.CIRCLE_MINOR.index(self.source_key)
                circle = self.CIRCLE_MINOR
            else:
                idx = self.CIRCLE_MAJOR.index(self.source_key)
                circle = self.CIRCLE_MAJOR
        except ValueError:
            # Si no está en el círculo, usar enarmónico
            key = self.ENHARMONICS.get(self.source_key, self.source_key)
            try:
                if self.is_minor:
                    idx = self.CIRCLE_MINOR.index(key)
                    circle = self.CIRCLE_MINOR
                else:
                    idx = self.CIRCLE_MAJOR.index(key)
                    circle = self.CIRCLE_MAJOR
            except ValueError:
                return {}

        # Paralelo
        if self.is_minor:
            related[KeyRelationship.PARALLEL] = (self.source_key, "major")
        else:
            related[KeyRelationship.PARALLEL] = (self.source_key, "minor")

        # Relativo
        if self.is_minor:
            rel_idx = self.CIRCLE_MAJOR.index(
                self.CIRCLE_MAJOR[(self.CIRCLE_MINOR.index(self.source_key)) % 12]
            ) if self.source_key in self.CIRCLE_MINOR else idx
            related[KeyRelationship.RELATIVE] = (self.CIRCLE_MAJOR[rel_idx], "major")
        else:
            minor_key = self.CIRCLE_MINOR[idx]
            related[KeyRelationship.RELATIVE] = (minor_key, "minor")

        # Dominante
        dom_idx = (idx + 1) % 12
        related[KeyRelationship.DOMINANT] = (
            circle[dom_idx],
            self.source_mode
        )

        # Subdominante
        sub_idx = (idx - 1) % 12
        related[KeyRelationship.SUBDOMINANT] = (
            circle[sub_idx],
            self.source_mode
        )

        # Mediante (relativo del dominante)
        if not self.is_minor:
            med_idx = (idx + 1) % 12
            related[KeyRelationship.MEDIANT] = (
                self.CIRCLE_MINOR[med_idx],
                "minor"
            )
        else:
            med_idx = (idx - 1) % 12
            related[KeyRelationship.MEDIANT] = (
                self.CIRCLE_MAJOR[med_idx],
                "major"
            )

        # Submediante
        if not self.is_minor:
            submed_idx = idx
            related[KeyRelationship.SUBMEDIANT] = (
                self.CIRCLE_MINOR[submed_idx],
                "minor"
            )
        else:
            submed_idx = idx
            related[KeyRelationship.SUBMEDIANT] = (
                self.CIRCLE_MAJOR[submed_idx],
                "major"
            )

        return related

    def find_pivot_chords(
        self,
        target_key: str,
        target_mode: str,
    ) -> List[PivotChord]:
        """
        Encuentra acordes pivote entre dos tonalidades.

        Args:
            target_key: Tonalidad destino
            target_mode: Modo destino

        Returns:
            Lista de posibles acordes pivote
        """
        pivots = []

        # Grados en mayor: I, ii, iii, IV, V, vi, vii°
        # Grados en menor: i, ii°, III, iv, v/V, VI, VII/vii°

        source_chords = self._get_diatonic_chords(self.source_key, self.source_mode)
        target_chords = self._get_diatonic_chords(target_key, target_mode)

        # Buscar acordes comunes
        for src_func, src_chord in source_chords.items():
            for tgt_func, tgt_chord in target_chords.items():
                if self._chords_match(src_chord, tgt_chord):
                    pivots.append(PivotChord(
                        chord_name=src_chord["name"],
                        function_in_source=src_func,
                        function_in_target=tgt_func,
                        common_tones=src_chord["notes"],
                    ))

        # Ordenar por calidad del pivote
        pivots.sort(key=lambda p: self._pivot_quality(p), reverse=True)

        return pivots

    def _get_diatonic_chords(
        self,
        key: str,
        mode: str,
    ) -> Dict[str, dict]:
        """Obtiene acordes diatónicos de una tonalidad."""
        # Simplificación: usar plantillas
        if mode in ["major", "ionian"]:
            # C mayor: C, Dm, Em, F, G, Am, Bdim
            template = [
                ("I", "maj", [0, 4, 7]),
                ("ii", "min", [2, 5, 9]),
                ("iii", "min", [4, 7, 11]),
                ("IV", "maj", [5, 9, 0]),
                ("V", "maj", [7, 11, 2]),
                ("vi", "min", [9, 0, 4]),
                ("vii°", "dim", [11, 2, 5]),
            ]
        else:  # menor
            # A menor: Am, Bdim, C, Dm, Em, F, G
            template = [
                ("i", "min", [0, 3, 7]),
                ("ii°", "dim", [2, 5, 8]),
                ("III", "maj", [3, 7, 10]),
                ("iv", "min", [5, 8, 0]),
                ("v", "min", [7, 10, 2]),
                ("V", "maj", [7, 11, 2]),  # Dominante armónico
                ("VI", "maj", [8, 0, 3]),
                ("VII", "maj", [10, 2, 5]),
            ]

        # Transponer a la tonalidad correcta
        root_offset = self._get_pitch_class(key)
        chords = {}

        for func, quality, intervals in template:
            notes = [(i + root_offset) % 12 for i in intervals]
            note_names = [self._pitch_class_to_name(n) for n in notes]
            chords[func] = {
                "name": note_names[0] + ("m" if quality == "min" else "" if quality == "maj" else "dim"),
                "notes": note_names,
                "quality": quality,
            }

        return chords

    def _get_pitch_class(self, note: str) -> int:
        """Convierte nombre de nota a clase de altura (0-11)."""
        pc_map = {
            "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11
        }
        base = note[0].upper()
        pc = pc_map.get(base, 0)

        if len(note) > 1:
            if note[1] == "#":
                pc = (pc + 1) % 12
            elif note[1] == "b":
                pc = (pc - 1) % 12

        return pc

    def _pitch_class_to_name(self, pc: int) -> str:
        """Convierte clase de altura a nombre de nota."""
        names = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
        return names[pc % 12]

    def _chords_match(self, chord1: dict, chord2: dict) -> bool:
        """Verifica si dos acordes son equivalentes."""
        # Comparar conjuntos de notas (ignorando orden)
        notes1 = set(self._get_pitch_class(n) for n in chord1["notes"])
        notes2 = set(self._get_pitch_class(n) for n in chord2["notes"])
        return notes1 == notes2

    def _pivot_quality(self, pivot: PivotChord) -> int:
        """Evalúa la calidad de un acorde pivote."""
        score = 0

        # Preferir acordes predominantes
        if pivot.function_in_target in ["ii", "IV", "ii°"]:
            score += 3
        # V es menos común como pivote pero posible
        if pivot.function_in_target == "V":
            score += 1
        # Funciones estables en origen
        if pivot.function_in_source in ["I", "i", "vi", "VI"]:
            score += 2

        return score

    def create_pivot_modulation(
        self,
        target_key: str,
        target_mode: str,
    ) -> ModulationPlan:
        """
        Crea plan de modulación por acorde pivote.

        Args:
            target_key: Tonalidad destino
            target_mode: Modo destino

        Returns:
            ModulationPlan con los detalles
        """
        pivots = self.find_pivot_chords(target_key, target_mode)

        if not pivots:
            # Sin pivote común, usar modulación directa
            return self.create_direct_modulation(target_key, target_mode)

        best_pivot = pivots[0]

        # Determinar grados melódicos de transición
        # Típicamente: notas del acorde pivote
        source_degrees = self._get_melodic_approach(best_pivot.function_in_source)
        target_degrees = self._get_melodic_confirmation(target_mode)

        return ModulationPlan(
            source_key=self.source_key,
            source_mode=self.source_mode,
            target_key=target_key,
            target_mode=target_mode,
            modulation_type=ModulationType.PIVOT_CHORD,
            pivot_chord=best_pivot,
            transition_measures=2,
            confirmation_cadence="authentic",
            melodic_degrees_source=source_degrees,
            melodic_degrees_target=target_degrees,
        )

    def create_direct_modulation(
        self,
        target_key: str,
        target_mode: str,
    ) -> ModulationPlan:
        """
        Crea modulación directa (sin acorde pivote).

        Útil para tonalidades lejanas o efectos dramáticos.

        Args:
            target_key: Tonalidad destino
            target_mode: Modo destino

        Returns:
            ModulationPlan
        """
        return ModulationPlan(
            source_key=self.source_key,
            source_mode=self.source_mode,
            target_key=target_key,
            target_mode=target_mode,
            modulation_type=ModulationType.DIRECT,
            transition_measures=1,
            confirmation_cadence="authentic",
            melodic_degrees_source=[5, 4, 3, 2],  # Descenso hacia V
            melodic_degrees_target=[7, 1],  # Sensible-tónica
        )

    def create_chromatic_modulation(
        self,
        target_key: str,
        target_mode: str,
        chromatic_note: int = 4,  # Grado a alterar cromáticamente
    ) -> ModulationPlan:
        """
        Crea modulación cromática.

        Usa una alteración cromática para introducir
        la nueva tonalidad gradualmente.

        Args:
            target_key: Tonalidad destino
            target_mode: Modo destino
            chromatic_note: Grado a alterar

        Returns:
            ModulationPlan
        """
        return ModulationPlan(
            source_key=self.source_key,
            source_mode=self.source_mode,
            target_key=target_key,
            target_mode=target_mode,
            modulation_type=ModulationType.CHROMATIC,
            transition_measures=2,
            confirmation_cadence="authentic",
            melodic_degrees_source=[1, 2, 3, chromatic_note],
            melodic_degrees_target=[5, 6, 7, 1],
        )

    def _get_melodic_approach(self, harmonic_function: str) -> List[int]:
        """Obtiene grados melódicos para aproximación al pivote."""
        approaches = {
            "I": [3, 2, 1],
            "i": [3, 2, 1],
            "ii": [4, 3, 2],
            "ii°": [4, 3, 2],
            "IV": [6, 5, 4],
            "iv": [6, 5, 4],
            "V": [7, 6, 5],
            "v": [7, 6, 5],
            "vi": [1, 7, 6],
            "VI": [1, 7, 6],
        }
        return approaches.get(harmonic_function, [5, 4, 3])

    def _get_melodic_confirmation(self, target_mode: str) -> List[int]:
        """Obtiene grados melódicos para confirmar nueva tonalidad."""
        if target_mode in ["major", "ionian"]:
            return [5, 4, 3, 2, 1]  # V-I melódico
        else:
            return [5, 4, 3, 2, 1]  # Similar en menor

    def suggest_modulation_for_section(
        self,
        section_name: str,
        relationship: KeyRelationship = None,
    ) -> ModulationPlan:
        """
        Sugiere modulación apropiada para una sección formal.

        Args:
            section_name: Nombre de la sección ("B", "development", etc.)
            relationship: Relación tonal deseada

        Returns:
            ModulationPlan sugerido
        """
        related = self.get_related_keys()

        # Defaults por sección
        if section_name in ["B", "contrasting", "episode"]:
            if relationship is None:
                relationship = KeyRelationship.DOMINANT
        elif section_name in ["development", "middle"]:
            if relationship is None:
                relationship = KeyRelationship.RELATIVE
        elif section_name in ["trio"]:
            if relationship is None:
                relationship = KeyRelationship.SUBDOMINANT

        if relationship and relationship in related:
            target_key, target_mode = related[relationship]
            return self.create_pivot_modulation(target_key, target_mode)

        # Fallback a dominante
        if KeyRelationship.DOMINANT in related:
            target_key, target_mode = related[KeyRelationship.DOMINANT]
            return self.create_pivot_modulation(target_key, target_mode)

        # Si todo falla, modulación directa a dominante
        return self.create_direct_modulation("G", "major")


def get_modulation_text(plan: ModulationPlan) -> str:
    """
    Genera texto descriptivo para una modulación.

    Args:
        plan: Plan de modulación

    Returns:
        Descripción textual
    """
    type_names = {
        ModulationType.PIVOT_CHORD: "por acorde pivote",
        ModulationType.DIRECT: "directa",
        ModulationType.CHROMATIC: "cromática",
        ModulationType.SEQUENTIAL: "secuencial",
        ModulationType.ENHARMONIC: "enarmónica",
    }

    text = f"Modulación {type_names.get(plan.modulation_type, '')} "
    text += f"de {plan.source_key} {plan.source_mode} "
    text += f"a {plan.target_key} {plan.target_mode}"

    if plan.pivot_chord:
        text += f"\nAcorde pivote: {plan.pivot_chord.chord_name} "
        text += f"({plan.pivot_chord.function_in_source} → {plan.pivot_chord.function_in_target})"

    return text
