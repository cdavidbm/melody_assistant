"""
Gestos cadenciales específicos.
Implementa patrones melódicos para diferentes tipos de cadencias.
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class CadenceType(Enum):
    """Tipos de cadencia."""
    AUTHENTIC_PERFECT = "pac"    # V-I, soprano en tónica
    AUTHENTIC_IMPERFECT = "iac"  # V-I, soprano no en tónica
    HALF = "hc"                  # Termina en V
    PLAGAL = "plagal"            # IV-I
    DECEPTIVE = "deceptive"      # V-vi
    PHRYGIAN = "phrygian"        # iv6-V (menor)
    EVADED = "evaded"            # V-? (cadencia evadida)


class CadenceStrength(Enum):
    """Fuerza de la cadencia."""
    STRONG = "strong"      # Final de sección/pieza
    MODERATE = "moderate"  # Final de frase
    WEAK = "weak"         # Articulación interna


@dataclass
class CadentialGesture:
    """
    Gesto melódico para una cadencia.

    Define los grados melódicos, ritmos y características
    del patrón cadencial.
    """
    cadence_type: CadenceType
    melody_degrees: List[int]      # Grados de la melodía (ej: [2, 1] para V-I)
    durations: List[Tuple[int, int]]  # Duraciones
    bass_degrees: List[int]        # Grados del bajo
    approach_degrees: List[int]    # Notas de aproximación opcionales
    has_suspension: bool = False   # Si incluye retardo
    suspension_degree: Optional[int] = None
    resolution_degree: Optional[int] = None
    ornament_type: Optional[str] = None  # Trino cadencial, etc.


class CadenceGenerator:
    """
    Genera gestos cadenciales idiomáticos.

    Los gestos cadenciales son fórmulas melódicas reconocibles
    que señalan finales de frase, sección o pieza.
    """

    def __init__(
        self,
        mode: str = "major",
        style: str = "classical",
    ):
        """
        Inicializa el generador.

        Args:
            mode: "major", "minor", etc.
            style: "baroque", "classical", "romantic"
        """
        self.mode = mode
        self.style = style
        self.is_minor = mode in ["minor", "harmonic_minor", "melodic_minor",
                                  "dorian", "phrygian", "aeolian", "locrian"]

    def get_authentic_cadence(
        self,
        perfect: bool = True,
        with_suspension: bool = False,
        strength: CadenceStrength = CadenceStrength.STRONG,
    ) -> CadentialGesture:
        """
        Genera cadencia auténtica (V-I).

        La cadencia auténtica perfecta tiene la melodía terminando en 1.
        La imperfecta puede terminar en 3 o 5.

        Args:
            perfect: Si es perfecta (melodía termina en 1)
            with_suspension: Si incluir retardo 4-3 o 7-6
            strength: Fuerza de la cadencia

        Returns:
            CadentialGesture para cadencia auténtica
        """
        if perfect:
            # Patrones comunes para PAC
            patterns = [
                [2, 1],      # re-do (más común)
                [7, 1],      # si-do (sensible)
                [4, 3, 2, 1],  # Escala descendente
                [5, 4, 3, 2, 1],  # Más elaborado
            ]
            melody = patterns[0] if strength == CadenceStrength.STRONG else patterns[1]
        else:
            # Patrones para IAC (termina en 3 o 5)
            patterns = [
                [2, 3],      # re-mi
                [4, 5],      # fa-sol
                [7, 1, 3],   # Tercera de tónica
            ]
            melody = patterns[0]

        # Duraciones según fuerza
        if strength == CadenceStrength.STRONG:
            durations = [(1, 2), (1, 1)]  # Blanca + redonda
        elif strength == CadenceStrength.MODERATE:
            durations = [(1, 4), (1, 2)]  # Negra + blanca
        else:
            durations = [(1, 4), (1, 4)]  # Dos negras

        # Ajustar longitudes
        while len(durations) < len(melody):
            durations.insert(0, (1, 8))

        gesture = CadentialGesture(
            cadence_type=CadenceType.AUTHENTIC_PERFECT if perfect else CadenceType.AUTHENTIC_IMPERFECT,
            melody_degrees=melody,
            durations=durations[:len(melody)],
            bass_degrees=[5, 1],
            approach_degrees=[4, 5] if self.style == "baroque" else [],
            has_suspension=with_suspension,
        )

        if with_suspension:
            gesture.suspension_degree = 4
            gesture.resolution_degree = 3

        # Trino cadencial en estilo barroco
        if self.style == "baroque" and strength == CadenceStrength.STRONG:
            gesture.ornament_type = "trill"

        return gesture

    def get_half_cadence(
        self,
        approach: str = "stepwise",
        strength: CadenceStrength = CadenceStrength.MODERATE,
    ) -> CadentialGesture:
        """
        Genera semicadencia (termina en V).

        La semicadencia crea expectativa y tensión.

        Args:
            approach: "stepwise" (por grado), "leap" (por salto)
            strength: Fuerza de la cadencia

        Returns:
            CadentialGesture para semicadencia
        """
        if approach == "stepwise":
            patterns = [
                [3, 2],      # mi-re (hacia dominante)
                [1, 7, 2],   # do-si-re
                [4, 3, 2],   # fa-mi-re
            ]
        else:
            patterns = [
                [5, 2],      # sol-re (salto de cuarta)
                [7, 2],      # Salto de tercera
            ]

        melody = patterns[0]

        if strength == CadenceStrength.MODERATE:
            durations = [(1, 4), (1, 2)]
        else:
            durations = [(1, 8), (1, 4)]

        while len(durations) < len(melody):
            durations.insert(0, (1, 8))

        return CadentialGesture(
            cadence_type=CadenceType.HALF,
            melody_degrees=melody,
            durations=durations[:len(melody)],
            bass_degrees=[4, 5] if len(melody) > 1 else [5],
            approach_degrees=[],
        )

    def get_plagal_cadence(
        self,
        strength: CadenceStrength = CadenceStrength.WEAK,
    ) -> CadentialGesture:
        """
        Genera cadencia plagal (IV-I).

        Conocida como "cadencia de Amén", tiene carácter conclusivo
        pero menos dramático que la auténtica.

        Args:
            strength: Fuerza de la cadencia

        Returns:
            CadentialGesture para cadencia plagal
        """
        # Patrones típicos (la melodía suele mantenerse en 1)
        patterns = [
            [4, 3, 1],   # fa-mi-do (más melódico)
            [6, 5, 1],   # la-sol-do
            [1, 1],      # Nota pedal en tónica
        ]

        melody = patterns[0] if strength != CadenceStrength.WEAK else patterns[2]

        if strength == CadenceStrength.STRONG:
            durations = [(1, 4), (1, 4), (1, 1)]
        else:
            durations = [(1, 4), (1, 2)]

        while len(durations) < len(melody):
            durations.insert(0, (1, 4))

        return CadentialGesture(
            cadence_type=CadenceType.PLAGAL,
            melody_degrees=melody,
            durations=durations[:len(melody)],
            bass_degrees=[4, 1],
            approach_degrees=[],
        )

    def get_deceptive_cadence(self) -> CadentialGesture:
        """
        Genera cadencia rota/engañosa (V-vi).

        Crea sorpresa al resolver a vi en lugar de I.
        Común para extensión de frases.

        Returns:
            CadentialGesture para cadencia engañosa
        """
        # La melodía suele ir a 1 pero la armonía va a vi
        patterns = [
            [7, 1],      # Sensible resuelve normalmente
            [2, 1],      # Pero en contexto de vi
            [2, 3],      # O sube a la tercera de vi
        ]

        melody = patterns[0]

        return CadentialGesture(
            cadence_type=CadenceType.DECEPTIVE,
            melody_degrees=melody,
            durations=[(1, 4), (1, 2)],
            bass_degrees=[5, 6],  # Bajo va a VI
            approach_degrees=[4],
        )

    def get_phrygian_cadence(self) -> CadentialGesture:
        """
        Genera cadencia frigia (iv6-V en menor).

        Característica del modo menor y música barroca.
        El bajo desciende por semitono.

        Returns:
            CadentialGesture para cadencia frigia
        """
        if not self.is_minor:
            # En mayor, adaptar
            melody = [4, 5]
            bass = [6, 5]
        else:
            # En menor, la cadencia frigia clásica
            melody = [4, 5]  # Grados melódicos
            bass = [6, 5]    # Bajo: b6-5

        return CadentialGesture(
            cadence_type=CadenceType.PHRYGIAN,
            melody_degrees=melody,
            durations=[(1, 2), (1, 2)],
            bass_degrees=bass,
            approach_degrees=[3, 4],
        )

    def get_cadential_trill(
        self,
        resolution_degree: int = 1,
    ) -> dict:
        """
        Genera especificaciones para trino cadencial.

        El trino cadencial (típicamente en 2) resuelve a la nota final.

        Args:
            resolution_degree: Grado de resolución

        Returns:
            Dict con especificaciones del trino
        """
        return {
            "trill_degree": resolution_degree + 1,  # Trino un grado arriba
            "resolution_degree": resolution_degree,
            "trill_duration": (1, 4),  # Al menos una negra
            "termination": True,  # Terminación típica
            "termination_notes": [resolution_degree + 1, resolution_degree - 1, resolution_degree],
        }

    def get_appoggiatura_cadential(
        self,
        target_degree: int = 1,
    ) -> dict:
        """
        Genera appoggiatura cadencial.

        Típico 4-3 sobre V antes de resolver a I.

        Args:
            target_degree: Grado objetivo

        Returns:
            Dict con especificaciones de la appoggiatura
        """
        return {
            "appoggiatura_degree": target_degree + 1,
            "resolution_degree": target_degree,
            "duration_ratio": 0.5,  # La appoggiatura toma la mitad del valor
            "accent": True,
        }

    def get_cadence_for_position(
        self,
        phrase_position: float,
        is_final: bool = False,
        previous_cadence: Optional[CadenceType] = None,
    ) -> CadentialGesture:
        """
        Selecciona el tipo de cadencia apropiado según el contexto.

        Args:
            phrase_position: Posición en la frase (0.0-1.0)
            is_final: Si es la cadencia final de la pieza
            previous_cadence: Cadencia anterior (para variedad)

        Returns:
            CadentialGesture apropiada
        """
        if is_final:
            # Final de pieza: siempre PAC
            return self.get_authentic_cadence(
                perfect=True,
                strength=CadenceStrength.STRONG,
            )

        if phrase_position < 0.5:
            # Primera mitad: semicadencia (crea expectativa)
            return self.get_half_cadence(strength=CadenceStrength.MODERATE)

        if phrase_position < 0.75:
            # Tercera cuarta parte: posible cadencia engañosa
            if previous_cadence != CadenceType.DECEPTIVE:
                return self.get_deceptive_cadence()
            else:
                return self.get_half_cadence()

        # Final de frase pero no de pieza
        return self.get_authentic_cadence(
            perfect=True,
            strength=CadenceStrength.MODERATE,
        )

    def suggest_cadence_progression(
        self,
        num_phrases: int = 4,
    ) -> List[CadenceType]:
        """
        Sugiere una progresión de cadencias para múltiples frases.

        Sigue patrones típicos del período clásico.

        Args:
            num_phrases: Número de frases

        Returns:
            Lista de tipos de cadencia
        """
        if num_phrases == 2:
            # Período simple: HC-PAC
            return [CadenceType.HALF, CadenceType.AUTHENTIC_PERFECT]

        if num_phrases == 4:
            # Período doble: HC-PAC-HC-PAC
            return [
                CadenceType.HALF,
                CadenceType.AUTHENTIC_IMPERFECT,
                CadenceType.HALF,
                CadenceType.AUTHENTIC_PERFECT,
            ]

        if num_phrases == 3:
            # Frase compuesta
            return [
                CadenceType.HALF,
                CadenceType.DECEPTIVE,
                CadenceType.AUTHENTIC_PERFECT,
            ]

        # Para más frases, alternar
        cadences = []
        for i in range(num_phrases):
            if i == num_phrases - 1:
                cadences.append(CadenceType.AUTHENTIC_PERFECT)
            elif i % 2 == 0:
                cadences.append(CadenceType.HALF)
            else:
                cadences.append(CadenceType.AUTHENTIC_IMPERFECT)

        return cadences


def get_lilypond_cadence_markup(
    cadence_type: CadenceType,
) -> str:
    """
    Genera markup LilyPond para indicar tipo de cadencia.

    Args:
        cadence_type: Tipo de cadencia

    Returns:
        Comando LilyPond para el markup
    """
    labels = {
        CadenceType.AUTHENTIC_PERFECT: "PAC",
        CadenceType.AUTHENTIC_IMPERFECT: "IAC",
        CadenceType.HALF: "HC",
        CadenceType.PLAGAL: "PC",
        CadenceType.DECEPTIVE: "DC",
        CadenceType.PHRYGIAN: "Phr",
        CadenceType.EVADED: "EC",
    }

    label = labels.get(cadence_type, "")
    if label:
        return f'^\\markup {{ \\italic {{ "{label}" }} }}'
    return ""


def get_roman_numeral_analysis(
    cadence_type: CadenceType,
    is_minor: bool = False,
) -> str:
    """
    Retorna análisis de números romanos para la cadencia.

    Args:
        cadence_type: Tipo de cadencia
        is_minor: Si está en modo menor

    Returns:
        String con análisis armónico
    """
    analyses = {
        CadenceType.AUTHENTIC_PERFECT: "V - I",
        CadenceType.AUTHENTIC_IMPERFECT: "V - I",
        CadenceType.HALF: "? - V",
        CadenceType.PLAGAL: "IV - I",
        CadenceType.DECEPTIVE: "V - vi" if not is_minor else "V - VI",
        CadenceType.PHRYGIAN: "iv⁶ - V" if is_minor else "iv⁶ - V",
        CadenceType.EVADED: "V - ?",
    }
    return analyses.get(cadence_type, "")
