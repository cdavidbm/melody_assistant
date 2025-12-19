"""
Secuencias melódicas y patrones de repetición.
Implementa secuencias diatónicas y cromáticas para desarrollo temático.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum


class SequenceType(Enum):
    """Tipos de secuencia melódica."""
    ASCENDING = "ascending"      # Secuencia ascendente
    DESCENDING = "descending"    # Secuencia descendente
    ASCENDING_THIRD = "asc_3rd"  # Sube por terceras
    DESCENDING_THIRD = "desc_3rd"  # Baja por terceras
    CIRCLE_OF_FIFTHS = "circle"  # Círculo de quintas descendente


class SequenceDirection(Enum):
    """Dirección de transposición."""
    UP = 1
    DOWN = -1


@dataclass
class MelodicSequence:
    """
    Representa una secuencia melódica.

    Una secuencia es la repetición de un patrón melódico
    a diferentes alturas, típicamente por grado conjunto.
    """
    pattern_degrees: List[int]  # Grados del patrón original (ej: [1, 2, 3, 2])
    pattern_durations: List[Tuple[int, int]]  # Duraciones del patrón
    num_repetitions: int = 3  # Número de repeticiones
    transposition_interval: int = 1  # Grados a transponer (1 = segunda)
    direction: SequenceDirection = SequenceDirection.UP
    sequence_type: SequenceType = SequenceType.ASCENDING

    def generate_sequence_degrees(self) -> List[List[int]]:
        """
        Genera todas las repeticiones de la secuencia.

        Returns:
            Lista de listas, cada una con los grados de una repetición
        """
        repetitions = []

        for rep in range(self.num_repetitions):
            offset = rep * self.transposition_interval * self.direction.value
            transposed = []

            for degree in self.pattern_degrees:
                new_degree = degree + offset
                # Normalizar a rango 1-7
                while new_degree > 7:
                    new_degree -= 7
                while new_degree < 1:
                    new_degree += 7
                transposed.append(new_degree)

            repetitions.append(transposed)

        return repetitions


class SequenceGenerator:
    """
    Genera secuencias melódicas para desarrollo temático.

    Las secuencias son fundamentales en la música barroca y clásica
    para crear direccionalidad y coherencia.
    """

    def __init__(self, scale_degrees: List[int] = None):
        """
        Inicializa el generador.

        Args:
            scale_degrees: Grados disponibles (default 1-7)
        """
        self.scale_degrees = scale_degrees or list(range(1, 8))

    def create_ascending_sequence(
        self,
        pattern: List[int],
        durations: List[Tuple[int, int]],
        repetitions: int = 3,
    ) -> MelodicSequence:
        """
        Crea una secuencia ascendente por grado conjunto.

        Ejemplo: C-D-E-D → D-E-F-E → E-F-G-F

        Args:
            pattern: Grados del patrón (ej: [1, 2, 3, 2])
            durations: Duraciones del patrón
            repetitions: Número de repeticiones

        Returns:
            MelodicSequence configurada
        """
        return MelodicSequence(
            pattern_degrees=pattern,
            pattern_durations=durations,
            num_repetitions=repetitions,
            transposition_interval=1,
            direction=SequenceDirection.UP,
            sequence_type=SequenceType.ASCENDING,
        )

    def create_descending_sequence(
        self,
        pattern: List[int],
        durations: List[Tuple[int, int]],
        repetitions: int = 3,
    ) -> MelodicSequence:
        """
        Crea una secuencia descendente por grado conjunto.

        Ejemplo: G-F-E-F → F-E-D-E → E-D-C-D
        """
        return MelodicSequence(
            pattern_degrees=pattern,
            pattern_durations=durations,
            num_repetitions=repetitions,
            transposition_interval=1,
            direction=SequenceDirection.DOWN,
            sequence_type=SequenceType.DESCENDING,
        )

    def create_thirds_sequence(
        self,
        pattern: List[int],
        durations: List[Tuple[int, int]],
        ascending: bool = True,
        repetitions: int = 3,
    ) -> MelodicSequence:
        """
        Crea una secuencia por terceras (común en Bach).

        Ascendente: C-E → D-F → E-G
        Descendente: G-E → F-D → E-C
        """
        return MelodicSequence(
            pattern_degrees=pattern,
            pattern_durations=durations,
            num_repetitions=repetitions,
            transposition_interval=2,  # Tercera = 2 grados
            direction=SequenceDirection.UP if ascending else SequenceDirection.DOWN,
            sequence_type=SequenceType.ASCENDING_THIRD if ascending else SequenceType.DESCENDING_THIRD,
        )

    def create_circle_sequence(
        self,
        pattern: List[int],
        durations: List[Tuple[int, int]],
        repetitions: int = 4,
    ) -> MelodicSequence:
        """
        Crea una secuencia de círculo de quintas descendente.

        Muy común en progresiones barrocas: I-IV-VII-III-VI-II-V-I
        Transpone por cuartas descendentes (= quintas ascendentes invertidas)
        """
        return MelodicSequence(
            pattern_degrees=pattern,
            pattern_durations=durations,
            num_repetitions=repetitions,
            transposition_interval=3,  # Cuarta = 3 grados
            direction=SequenceDirection.DOWN,
            sequence_type=SequenceType.CIRCLE_OF_FIFTHS,
        )

    def detect_sequence_opportunity(
        self,
        recent_degrees: List[int],
        min_pattern_length: int = 3,
    ) -> Optional[MelodicSequence]:
        """
        Detecta si hay una oportunidad para crear una secuencia
        basada en las notas recientes.

        Args:
            recent_degrees: Grados recientes de la melodía
            min_pattern_length: Longitud mínima del patrón

        Returns:
            MelodicSequence si se detecta patrón, None si no
        """
        if len(recent_degrees) < min_pattern_length:
            return None

        # Buscar patrón repetible en las últimas notas
        pattern = recent_degrees[-min_pattern_length:]

        # Verificar si el patrón tiene movimiento interesante
        movements = [
            pattern[i+1] - pattern[i]
            for i in range(len(pattern) - 1)
        ]

        # Si hay movimiento, es buen candidato para secuencia
        if any(m != 0 for m in movements):
            # Determinar dirección general
            avg_movement = sum(movements) / len(movements)

            if avg_movement > 0:
                return self.create_ascending_sequence(
                    pattern=pattern,
                    durations=[(1, 8)] * len(pattern),
                    repetitions=3,
                )
            else:
                return self.create_descending_sequence(
                    pattern=pattern,
                    durations=[(1, 8)] * len(pattern),
                    repetitions=3,
                )

        return None

    def should_use_sequence(
        self,
        measure_index: int,
        num_measures: int,
        phrase_position: float,
    ) -> bool:
        """
        Determina si es buen momento para usar una secuencia.

        Las secuencias son más comunes en:
        - Desarrollo (mitad de la pieza)
        - Transiciones entre frases
        - Aproximación al clímax

        Args:
            measure_index: Índice del compás actual
            num_measures: Total de compases
            phrase_position: Posición en la frase (0.0 - 1.0)

        Returns:
            True si es buen momento para secuencia
        """
        progress = measure_index / max(1, num_measures - 1)

        # Buenas posiciones para secuencias:
        # - Entre 30% y 70% de la pieza (desarrollo)
        # - No al principio ni al final
        if 0.3 <= progress <= 0.7:
            # Más probable cerca del clímax
            if 0.4 <= phrase_position <= 0.6:
                return True

        return False

    def get_common_patterns(self) -> List[List[int]]:
        """
        Retorna patrones comunes para secuencias.

        Estos patrones son típicos en música barroca y clásica.
        """
        return [
            # Patrones de 3 notas
            [1, 2, 3],      # Escala ascendente
            [3, 2, 1],      # Escala descendente
            [1, 3, 2],      # Bordadura superior
            [1, 2, 1],      # Bordadura inferior

            # Patrones de 4 notas
            [1, 2, 3, 2],   # Arco ascendente
            [3, 2, 1, 2],   # Arco descendente
            [1, 3, 2, 4],   # Zigzag ascendente
            [4, 2, 3, 1],   # Zigzag descendente

            # Patrones de 5 notas (más elaborados)
            [1, 2, 3, 4, 3],    # Escala con retorno
            [5, 4, 3, 2, 1],    # Escala descendente completa
            [1, 3, 2, 4, 3],    # Terceras quebradas ascendentes
        ]
