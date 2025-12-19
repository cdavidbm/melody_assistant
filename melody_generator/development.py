"""
Desarrollo motívico avanzado.
Implementa técnicas de desarrollo temático: fragmentación, liquidación,
expansión interválica, desplazamiento rítmico, combinación de motivos.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum
import random
import copy

from .models import Motif, RhythmicPattern


class DevelopmentTechnique(Enum):
    """Técnicas de desarrollo motívico."""
    FRAGMENTATION = "fragmentation"       # Usar solo parte del motivo
    EXTENSION = "extension"               # Extender el motivo
    EXPANSION = "expansion"               # Expandir intervalos
    CONTRACTION = "contraction"           # Contraer intervalos
    DISPLACEMENT = "displacement"          # Desplazamiento métrico
    LIQUIDATION = "liquidation"           # Simplificación gradual
    COMBINATION = "combination"           # Combinar dos motivos
    INTERPOLATION = "interpolation"       # Insertar notas entre
    ELISION = "elision"                   # Superponer final/inicio
    STRETTO = "stretto"                   # Entrada anticipada


@dataclass
class DevelopmentPlan:
    """
    Plan de desarrollo para una sección.

    Define qué técnicas aplicar y en qué orden.
    """
    techniques: List[DevelopmentTechnique]
    intensity_curve: List[float]  # 0.0-1.0 por cada aplicación
    target_length: int            # Longitud objetivo en notas
    climax_position: float = 0.7  # Posición del clímax (0.0-1.0)


class MotivicDeveloper:
    """
    Desarrolla motivos usando técnicas de composición clásica.

    El desarrollo motívico es fundamental para crear coherencia
    y variedad en la música. Estas técnicas son usadas por
    compositores desde Bach hasta Brahms.
    """

    def __init__(
        self,
        intensity_level: int = 2,  # 1=conservador, 2=moderado, 3=intenso
    ):
        """
        Inicializa el desarrollador de motivos.

        Args:
            intensity_level: Nivel de intensidad del desarrollo
        """
        self.intensity_level = intensity_level

    def fragment(
        self,
        motif: Motif,
        fragment_type: str = "head",
        fragment_length: int = None,
    ) -> Motif:
        """
        Fragmenta un motivo, tomando solo una parte.

        La fragmentación es fundamental en el desarrollo.
        Beethoven la usaba extensivamente.

        Args:
            motif: Motivo original
            fragment_type: "head" (inicio), "tail" (final), "middle" (medio)
            fragment_length: Longitud del fragmento (None = automático)

        Returns:
            Motif fragmentado
        """
        if len(motif.pitches) <= 2:
            return motif

        if fragment_length is None:
            fragment_length = max(2, len(motif.pitches) // 2)

        fragment_length = min(fragment_length, len(motif.pitches))

        if fragment_type == "head":
            pitches = motif.pitches[:fragment_length]
            degrees = motif.degrees[:fragment_length]
            intervals = motif.intervals[:fragment_length - 1] if motif.intervals else []
            durations = motif.rhythm.durations[:fragment_length]
        elif fragment_type == "tail":
            pitches = motif.pitches[-fragment_length:]
            degrees = motif.degrees[-fragment_length:]
            intervals = motif.intervals[-(fragment_length - 1):] if motif.intervals else []
            durations = motif.rhythm.durations[-fragment_length:]
        else:  # middle
            start = (len(motif.pitches) - fragment_length) // 2
            end = start + fragment_length
            pitches = motif.pitches[start:end]
            degrees = motif.degrees[start:end]
            intervals = motif.intervals[start:end - 1] if len(motif.intervals) > start else []
            durations = motif.rhythm.durations[start:end]

        return Motif(
            pitches=pitches,
            intervals=intervals,
            rhythm=RhythmicPattern(
                durations=durations,
                strong_beat_indices=[0] if durations else [],
            ),
            degrees=degrees,
        )

    def extend(
        self,
        motif: Motif,
        extension_type: str = "sequence",
        extension_length: int = 2,
    ) -> Motif:
        """
        Extiende un motivo añadiendo notas.

        Args:
            motif: Motivo original
            extension_type: "sequence" (secuencia), "echo" (repetición),
                          "cadential" (hacia cadencia)
            extension_length: Notas a añadir

        Returns:
            Motif extendido
        """
        if extension_type == "sequence":
            # Continuar el patrón interválico
            extension = self._create_sequence_extension(motif, extension_length)
        elif extension_type == "echo":
            # Repetir las últimas notas
            extension = self._create_echo_extension(motif, extension_length)
        else:  # cadential
            # Dirigirse hacia la tónica
            extension = self._create_cadential_extension(motif, extension_length)

        # Combinar original con extensión
        new_pitches = motif.pitches + extension["pitches"]
        new_degrees = motif.degrees + extension["degrees"]
        new_durations = list(motif.rhythm.durations) + extension["durations"]

        # Recalcular intervalos
        new_intervals = motif.intervals.copy() if motif.intervals else []
        for i in range(len(motif.pitches) - 1, len(new_pitches) - 1):
            if i < len(new_pitches) - 1:
                new_intervals.append(0)  # Placeholder

        return Motif(
            pitches=new_pitches,
            intervals=new_intervals,
            rhythm=RhythmicPattern(
                durations=new_durations,
                strong_beat_indices=motif.rhythm.strong_beat_indices,
            ),
            degrees=new_degrees,
        )

    def _create_sequence_extension(
        self,
        motif: Motif,
        length: int,
    ) -> dict:
        """Crea extensión por secuencia."""
        # Transponer el patrón un grado
        last_degrees = motif.degrees[-min(2, len(motif.degrees)):]
        step = 1 if len(motif.degrees) <= 1 else motif.degrees[-1] - motif.degrees[-2]

        new_degrees = []
        for i in range(length):
            base = last_degrees[-1] if new_degrees == [] else new_degrees[-1]
            new_deg = base + step
            while new_deg > 7:
                new_deg -= 7
            while new_deg < 1:
                new_deg += 7
            new_degrees.append(new_deg)

        return {
            "pitches": ["C4"] * length,  # Placeholder - se resuelve con ScaleManager
            "degrees": new_degrees,
            "durations": [(1, 8)] * length,
        }

    def _create_echo_extension(
        self,
        motif: Motif,
        length: int,
    ) -> dict:
        """Crea extensión por eco."""
        # Repetir las últimas notas
        echo_degrees = motif.degrees[-min(length, len(motif.degrees)):]
        while len(echo_degrees) < length:
            echo_degrees = echo_degrees + echo_degrees[:length - len(echo_degrees)]

        return {
            "pitches": ["C4"] * length,
            "degrees": echo_degrees[:length],
            "durations": [(1, 8)] * length,
        }

    def _create_cadential_extension(
        self,
        motif: Motif,
        length: int,
    ) -> dict:
        """Crea extensión cadencial (hacia tónica)."""
        last_degree = motif.degrees[-1] if motif.degrees else 5
        cadential_pattern = []

        # Descender hacia 1
        current = last_degree
        for i in range(length):
            if current > 1:
                current -= 1
            cadential_pattern.append(current)

        return {
            "pitches": ["C4"] * length,
            "degrees": cadential_pattern,
            "durations": [(1, 4)] * length,  # Más largos para cadencia
        }

    def expand_intervals(
        self,
        motif: Motif,
        factor: float = 1.5,
    ) -> Motif:
        """
        Expande los intervalos del motivo.

        Útil para crear tensión y ampliar el rango melódico.

        Args:
            motif: Motivo original
            factor: Factor de expansión (1.5 = 50% más grande)

        Returns:
            Motif con intervalos expandidos
        """
        if not motif.intervals:
            return motif

        new_intervals = []
        for interval in motif.intervals:
            expanded = int(interval * factor)
            # Limitar a una octava
            expanded = max(-12, min(12, expanded))
            new_intervals.append(expanded)

        # Recalcular pitches
        new_pitches = [motif.pitches[0]]
        new_degrees = [motif.degrees[0]]

        for interval in new_intervals:
            # Calcular nuevo grado (simplificado)
            prev_degree = new_degrees[-1]
            step = 1 if interval > 0 else -1
            steps = abs(interval) // 2  # Aproximación
            new_deg = prev_degree + (step * steps)
            while new_deg > 7:
                new_deg -= 7
            while new_deg < 1:
                new_deg += 7
            new_degrees.append(new_deg)
            new_pitches.append("C4")  # Placeholder

        return Motif(
            pitches=new_pitches,
            intervals=new_intervals,
            rhythm=motif.rhythm,
            degrees=new_degrees,
        )

    def contract_intervals(
        self,
        motif: Motif,
        factor: float = 0.5,
    ) -> Motif:
        """
        Contrae los intervalos del motivo.

        Útil para reducir tensión y crear estabilidad.

        Args:
            motif: Motivo original
            factor: Factor de contracción (0.5 = mitad)

        Returns:
            Motif con intervalos contraídos
        """
        return self.expand_intervals(motif, factor)

    def displace_metrically(
        self,
        motif: Motif,
        displacement: Tuple[int, int] = (1, 8),
    ) -> Motif:
        """
        Desplaza el motivo métricamente.

        El desplazamiento rítmico crea interés y tensión.

        Args:
            motif: Motivo original
            displacement: Desplazamiento como fracción (ej: (1, 8) = una corchea)

        Returns:
            Motif desplazado
        """
        # Añadir silencio al inicio (representado con nota corta)
        new_durations = [displacement] + list(motif.rhythm.durations)

        # Ajustar índices de tiempo fuerte
        new_strong = [i + 1 for i in motif.rhythm.strong_beat_indices]

        return Motif(
            pitches=["r"] + motif.pitches,  # r = rest placeholder
            intervals=[0] + motif.intervals if motif.intervals else [],
            rhythm=RhythmicPattern(
                durations=new_durations,
                strong_beat_indices=new_strong,
            ),
            degrees=[0] + motif.degrees,  # 0 = rest
        )

    def liquidate(
        self,
        motif: Motif,
        stage: int = 1,
    ) -> Motif:
        """
        Aplica liquidación (simplificación gradual).

        La liquidación reduce el motivo hacia la cadencia,
        técnica característica de Beethoven.

        Args:
            motif: Motivo original
            stage: Etapa de liquidación (1=leve, 2=medio, 3=severo)

        Returns:
            Motif simplificado
        """
        if stage == 1:
            # Etapa 1: Fragmentar al inicio
            return self.fragment(motif, "head", len(motif.pitches) - 1)

        elif stage == 2:
            # Etapa 2: Solo 2-3 notas, ritmo simplificado
            fragment = self.fragment(motif, "head", min(3, len(motif.pitches)))
            # Simplificar ritmo
            simple_durations = [(1, 4)] * len(fragment.pitches)
            return Motif(
                pitches=fragment.pitches,
                intervals=fragment.intervals,
                rhythm=RhythmicPattern(
                    durations=simple_durations,
                    strong_beat_indices=[0],
                ),
                degrees=fragment.degrees,
            )

        else:
            # Etapa 3: Una o dos notas
            if len(motif.pitches) >= 2:
                pitches = [motif.pitches[0], motif.pitches[-1]]
                degrees = [motif.degrees[0], motif.degrees[-1]]
            else:
                pitches = motif.pitches[:1]
                degrees = motif.degrees[:1]

            return Motif(
                pitches=pitches,
                intervals=[],
                rhythm=RhythmicPattern(
                    durations=[(1, 2)] * len(pitches),
                    strong_beat_indices=[0],
                ),
                degrees=degrees,
            )

    def interpolate(
        self,
        motif: Motif,
        position: int = 1,
        note_degree: int = None,
    ) -> Motif:
        """
        Interpola una nota dentro del motivo.

        Args:
            motif: Motivo original
            position: Posición donde insertar
            note_degree: Grado de la nota a insertar (None = automático)

        Returns:
            Motif con nota interpolada
        """
        if position < 0 or position >= len(motif.pitches):
            position = 1

        # Calcular grado intermedio si no se especifica
        if note_degree is None:
            if position < len(motif.degrees) and position > 0:
                prev_deg = motif.degrees[position - 1]
                next_deg = motif.degrees[position]
                note_degree = (prev_deg + next_deg) // 2
                if note_degree < 1:
                    note_degree = 1
            else:
                note_degree = 3

        new_pitches = (
            motif.pitches[:position] +
            ["C4"] +  # Placeholder
            motif.pitches[position:]
        )
        new_degrees = (
            motif.degrees[:position] +
            [note_degree] +
            motif.degrees[position:]
        )
        new_durations = (
            list(motif.rhythm.durations[:position]) +
            [(1, 16)] +  # Nota corta interpolada
            list(motif.rhythm.durations[position:])
        )

        return Motif(
            pitches=new_pitches,
            intervals=[],
            rhythm=RhythmicPattern(
                durations=new_durations,
                strong_beat_indices=motif.rhythm.strong_beat_indices,
            ),
            degrees=new_degrees,
        )

    def elide(
        self,
        motif1: Motif,
        motif2: Motif,
    ) -> Motif:
        """
        Elide dos motivos (superponer final de uno con inicio de otro).

        La elisión crea continuidad y momentum.

        Args:
            motif1: Primer motivo
            motif2: Segundo motivo

        Returns:
            Motif con elisión
        """
        if not motif1.pitches or not motif2.pitches:
            return motif1 if motif1.pitches else motif2

        # Combinar: todo de motif1 excepto última nota + todo de motif2
        new_pitches = motif1.pitches[:-1] + motif2.pitches
        new_degrees = motif1.degrees[:-1] + motif2.degrees

        # Combinar duraciones
        new_durations = list(motif1.rhythm.durations[:-1])

        # La nota de elisión toma la duración mayor
        last_dur1 = motif1.rhythm.durations[-1] if motif1.rhythm.durations else (1, 4)
        first_dur2 = motif2.rhythm.durations[0] if motif2.rhythm.durations else (1, 4)

        # Elegir la más larga
        if last_dur1[0] / last_dur1[1] >= first_dur2[0] / first_dur2[1]:
            elided_dur = last_dur1
        else:
            elided_dur = first_dur2

        new_durations.append(elided_dur)
        new_durations.extend(motif2.rhythm.durations[1:])

        return Motif(
            pitches=new_pitches,
            intervals=[],
            rhythm=RhythmicPattern(
                durations=new_durations,
                strong_beat_indices=[0],
            ),
            degrees=new_degrees,
        )

    def create_development_plan(
        self,
        num_measures: int,
        style: str = "classical",
    ) -> DevelopmentPlan:
        """
        Crea un plan de desarrollo para una sección.

        Args:
            num_measures: Número de compases a desarrollar
            style: "baroque", "classical", "romantic"

        Returns:
            DevelopmentPlan con técnicas a aplicar
        """
        if style == "baroque":
            # Barroco: mucha secuencia y fragmentación
            techniques = [
                DevelopmentTechnique.FRAGMENTATION,
                DevelopmentTechnique.EXTENSION,
                DevelopmentTechnique.FRAGMENTATION,
                DevelopmentTechnique.EXPANSION,
            ]
        elif style == "romantic":
            # Romántico: transformación más libre
            techniques = [
                DevelopmentTechnique.EXPANSION,
                DevelopmentTechnique.INTERPOLATION,
                DevelopmentTechnique.DISPLACEMENT,
                DevelopmentTechnique.CONTRACTION,
                DevelopmentTechnique.LIQUIDATION,
            ]
        else:
            # Clásico: balance de técnicas
            techniques = [
                DevelopmentTechnique.FRAGMENTATION,
                DevelopmentTechnique.EXTENSION,
                DevelopmentTechnique.EXPANSION,
                DevelopmentTechnique.LIQUIDATION,
            ]

        # Generar curva de intensidad
        intensity = []
        for i in range(len(techniques)):
            progress = i / max(1, len(techniques) - 1)
            # Subir hacia clímax, bajar después
            if progress < 0.7:
                int_value = 0.3 + (progress / 0.7) * 0.7
            else:
                int_value = 1.0 - ((progress - 0.7) / 0.3) * 0.5
            intensity.append(int_value)

        return DevelopmentPlan(
            techniques=techniques,
            intensity_curve=intensity,
            target_length=num_measures * 4,  # Aproximado
            climax_position=0.7,
        )

    def apply_development_plan(
        self,
        motif: Motif,
        plan: DevelopmentPlan,
    ) -> List[Motif]:
        """
        Aplica un plan de desarrollo a un motivo.

        Args:
            motif: Motivo base
            plan: Plan de desarrollo

        Returns:
            Lista de motivos desarrollados
        """
        results = [motif]  # Empezar con original
        current = motif

        for i, technique in enumerate(plan.techniques):
            intensity = plan.intensity_curve[i] if i < len(plan.intensity_curve) else 0.5

            if technique == DevelopmentTechnique.FRAGMENTATION:
                # Más intensidad = fragmentos más cortos
                frag_len = max(2, int(len(current.pitches) * (1 - intensity * 0.5)))
                current = self.fragment(current, "head", frag_len)

            elif technique == DevelopmentTechnique.EXTENSION:
                ext_len = int(2 + intensity * 3)
                current = self.extend(current, "sequence", ext_len)

            elif technique == DevelopmentTechnique.EXPANSION:
                factor = 1 + intensity * 0.5
                current = self.expand_intervals(current, factor)

            elif technique == DevelopmentTechnique.CONTRACTION:
                factor = 1 - intensity * 0.4
                current = self.contract_intervals(current, max(0.3, factor))

            elif technique == DevelopmentTechnique.DISPLACEMENT:
                if intensity > 0.5:
                    current = self.displace_metrically(current, (1, 8))

            elif technique == DevelopmentTechnique.LIQUIDATION:
                stage = min(3, int(intensity * 3) + 1)
                current = self.liquidate(current, stage)

            elif technique == DevelopmentTechnique.INTERPOLATION:
                if len(current.pitches) >= 2:
                    current = self.interpolate(current, 1)

            results.append(current)

        return results


def analyze_motivic_relationship(
    motif1: Motif,
    motif2: Motif,
) -> dict:
    """
    Analiza la relación entre dos motivos.

    Args:
        motif1: Primer motivo
        motif2: Segundo motivo

    Returns:
        Dict con análisis de relación
    """
    analysis = {
        "is_related": False,
        "relationship_type": None,
        "similarity_score": 0.0,
        "shared_degrees": [],
        "intervallic_similarity": 0.0,
    }

    if not motif1.degrees or not motif2.degrees:
        return analysis

    # Grados compartidos
    set1 = set(motif1.degrees)
    set2 = set(motif2.degrees)
    shared = set1.intersection(set2)
    analysis["shared_degrees"] = list(shared)

    # Similaridad de grados
    min_len = min(len(motif1.degrees), len(motif2.degrees))
    matches = sum(1 for i in range(min_len)
                  if motif1.degrees[i] == motif2.degrees[i])
    degree_sim = matches / min_len if min_len > 0 else 0

    # Similaridad interválica
    if motif1.intervals and motif2.intervals:
        min_int_len = min(len(motif1.intervals), len(motif2.intervals))
        int_matches = sum(1 for i in range(min_int_len)
                         if motif1.intervals[i] == motif2.intervals[i])
        analysis["intervallic_similarity"] = int_matches / min_int_len if min_int_len > 0 else 0

    # Score total
    analysis["similarity_score"] = (degree_sim * 0.5 +
                                     analysis["intervallic_similarity"] * 0.3 +
                                     len(shared) / 7 * 0.2)

    # Determinar tipo de relación
    if analysis["similarity_score"] > 0.8:
        analysis["relationship_type"] = "nearly_identical"
        analysis["is_related"] = True
    elif analysis["similarity_score"] > 0.5:
        analysis["relationship_type"] = "variation"
        analysis["is_related"] = True
    elif analysis["similarity_score"] > 0.3:
        analysis["relationship_type"] = "derived"
        analysis["is_related"] = True
    elif len(shared) >= 2:
        analysis["relationship_type"] = "loosely_related"
        analysis["is_related"] = True

    return analysis
