"""
Algoritmos geneticos para evolucion de melodias.
Usa DEAP como framework de GA.

Arquitectura SOLID:
- SRP: Cada clase tiene una responsabilidad unica
- OCP: Extensible via nuevos operadores geneticos sin modificar existentes
- LSP: GeneticMelodyEvolver puede ser inyectado donde se necesite un generador
- ISP: Interfaces minimas y especificas
- DIP: Depende de abstracciones (ScaleManager, HarmonyManager, etc.)

El sistema evoluciona motivos musicales manteniendo coherencia modal:
- El cromosoma usa grados de escala (1-7), no semitonos
- Cada modo tiene su propia escala diatonica (C Lidio = F# natural, no cromatico)
- La fitness function premia uso de notas caracteristicas del modo
"""

import logging
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Set, Callable
from statistics import mean

from deap import base, creator, tools

from music21 import pitch

from .models import Motif, RhythmicPattern, MotivicVariation, Period, Phrase, Semiphrase, HarmonicFunction
from .scales import ScaleManager
from .harmony import HarmonyManager
from .scoring import MelodicScorer, NoteCandidate, MetricStrength, PhrasePosition

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURACION
# ============================================================================

# Duraciones validas para LilyPond (potencias de 2)
VALID_DURATIONS: List[Tuple[int, int]] = [
    (1, 16),  # semicorchea
    (1, 8),   # corchea
    (3, 16),  # corchea con puntillo
    (1, 4),   # negra
    (3, 8),   # negra con puntillo
    (1, 2),   # blanca
]

# Notas caracteristicas por modo (color notes que definen el modo)
# Estas notas DEBEN ser enfatizadas, no evitadas
MODE_CHARACTERISTIC_DEGREES: Dict[str, int] = {
    "lydian": 4,        # #4 (vs major)
    "mixolydian": 7,    # b7 (vs major)
    "dorian": 6,        # nat6 (vs minor)
    "phrygian": 2,      # b2 (vs minor)
    "locrian": 5,       # b5 (vs minor)
    # Modos sin nota caracteristica distintiva usan tonica
    "major": 1,
    "minor": 3,         # La 3a menor define el modo menor
    "harmonic_minor": 7,  # Sensible
    "melodic_minor": 6,   # 6a y 7a elevadas
}


@dataclass
class GeneticConfig:
    """Configuracion para algoritmos geneticos."""

    enabled: bool = False
    generations: int = 15
    population_size: int = 30
    crossover_prob: float = 0.7
    mutation_prob: float = 0.3
    elitism: int = 2
    motif_length: Tuple[int, int] = (4, 6)  # min, max notas
    use_markov_polish: bool = True

    # Pesos de fitness (suman ~1.0)
    fitness_weights: Dict[str, float] = field(default_factory=lambda: {
        "voice_leading": 0.25,
        "harmonic": 0.20,
        "contour": 0.15,
        "rhythm": 0.15,
        "development": 0.15,
        "range": 0.10,
    })

    def __post_init__(self):
        """Valida configuracion."""
        if not 5 <= self.generations <= 100:
            logger.warning(f"generations={self.generations} fuera del rango recomendado (5-100)")
        if not 10 <= self.population_size <= 200:
            logger.warning(f"population_size={self.population_size} fuera del rango recomendado (10-200)")
        if not 0.0 <= self.crossover_prob <= 1.0:
            raise ValueError(f"crossover_prob debe estar entre 0.0 y 1.0")
        if not 0.0 <= self.mutation_prob <= 1.0:
            raise ValueError(f"mutation_prob debe estar entre 0.0 y 1.0")


# ============================================================================
# REPRESENTACION DEL CROMOSOMA
# ============================================================================

@dataclass
class MotifGene:
    """
    Un gen = una nota del motivo.

    Usa grados de escala (1-7) en lugar de semitonos para garantizar
    que el resultado siempre sea diatonico al modo actual.
    """
    degree: int           # Grado de escala (1-7)
    octave_offset: int    # -1, 0, +1 respecto a octava base
    duration_idx: int     # Indice en VALID_DURATIONS

    def __post_init__(self):
        """Valida y normaliza valores."""
        # Normalizar grado a 1-7
        self.degree = ((self.degree - 1) % 7) + 1
        # Limitar offset de octava
        self.octave_offset = max(-1, min(1, self.octave_offset))
        # Limitar indice de duracion
        self.duration_idx = max(0, min(len(VALID_DURATIONS) - 1, self.duration_idx))

    def get_duration(self) -> Tuple[int, int]:
        """Retorna la duracion como tupla (numerador, denominador)."""
        return VALID_DURATIONS[self.duration_idx]

    def clone(self) -> "MotifGene":
        """Crea una copia del gen."""
        return MotifGene(
            degree=self.degree,
            octave_offset=self.octave_offset,
            duration_idx=self.duration_idx
        )


# ============================================================================
# CONTEXTO GENETICO
# ============================================================================

@dataclass
class GeneticContext:
    """
    Contexto musical para la evaluacion genetica.

    Encapsula todas las dependencias necesarias para evaluar
    y convertir cromosomas a estructuras musicales.
    """
    scale_manager: ScaleManager
    harmony_manager: HarmonyManager
    config: GeneticConfig
    base_octave: int = 4

    # Cache de pitch classes del modo actual
    _modal_pitch_classes: Optional[Set[int]] = field(default=None, repr=False)

    def __post_init__(self):
        """Inicializa cache de pitch classes."""
        self._modal_pitch_classes = self._compute_modal_pitch_classes()

    def _compute_modal_pitch_classes(self) -> Set[int]:
        """
        Obtiene los pitch classes diatonicos para el modo actual.

        IMPORTANTE: Usa ScaleManager, no templates fijos mayor/menor.
        Esto asegura que C Lidio tenga F# como diatonico.
        """
        scale_pitches = self.scale_manager.get_scale_pitches()
        return {pitch.Pitch(p).pitchClass for p in scale_pitches}

    def get_modal_pitch_classes(self) -> Set[int]:
        """Retorna pitch classes diatonicos del modo."""
        if self._modal_pitch_classes is None:
            self._modal_pitch_classes = self._compute_modal_pitch_classes()
        return self._modal_pitch_classes

    def get_characteristic_degree(self) -> int:
        """Retorna el grado caracteristico del modo actual."""
        return MODE_CHARACTERISTIC_DEGREES.get(self.scale_manager.mode, 1)

    def gene_to_pitch(self, gene: MotifGene) -> str:
        """Convierte un gen a string de pitch."""
        octave = self.base_octave + gene.octave_offset
        return self.scale_manager.get_pitch_by_degree(gene.degree, octave)

    def is_in_range(self, gene: MotifGene) -> bool:
        """Verifica si el pitch del gen esta en el rango melodico."""
        try:
            pitch_str = self.gene_to_pitch(gene)
            p = pitch.Pitch(pitch_str)
            return self.scale_manager.is_in_range(p)
        except Exception:
            return False


# ============================================================================
# EVALUADOR DE FITNESS
# ============================================================================

class MotifFitnessEvaluator:
    """
    Evalua la calidad de un cromosoma (motivo).

    Usa el sistema de scoring existente (MelodicScorer) y anade
    criterios especificos para la evolucion genetica.
    """

    def __init__(self, context: GeneticContext):
        """
        Inicializa el evaluador.

        Args:
            context: Contexto genetico con dependencias
        """
        self.context = context
        self.weights = context.config.fitness_weights

    def evaluate(self, chromosome: List[MotifGene]) -> Tuple[float, ...]:
        """
        Evalua fitness del cromosoma.

        Args:
            chromosome: Lista de genes (notas del motivo)

        Returns:
            Tupla de scores para DEAP (multi-objetivo compatible)
        """
        if not chromosome:
            return (0.0,)

        # Calcular scores individuales
        voice_leading = self._score_voice_leading(chromosome)
        harmonic = self._score_harmonic(chromosome)
        contour = self._score_contour(chromosome)
        rhythm = self._score_rhythmic_interest(chromosome)
        development = self._score_development_potential(chromosome)
        range_score = self._score_range(chromosome)

        # Score total ponderado
        total = (
            voice_leading * self.weights.get("voice_leading", 0.25) +
            harmonic * self.weights.get("harmonic", 0.20) +
            contour * self.weights.get("contour", 0.15) +
            rhythm * self.weights.get("rhythm", 0.15) +
            development * self.weights.get("development", 0.15) +
            range_score * self.weights.get("range", 0.10)
        )

        return (total,)

    def _score_voice_leading(self, chromosome: List[MotifGene]) -> float:
        """Evalua conduccion de voces (preferir grados conjuntos)."""
        if len(chromosome) < 2:
            return 0.8

        scores = []
        for i in range(1, len(chromosome)):
            prev_gene = chromosome[i - 1]
            curr_gene = chromosome[i]

            # Calcular intervalo en grados
            degree_diff = abs(curr_gene.degree - prev_gene.degree)
            octave_diff = abs(curr_gene.octave_offset - prev_gene.octave_offset)

            # Penalizar saltos de octava
            if octave_diff > 0:
                degree_diff += 7 * octave_diff

            # Scoring: segundas ideal, terceras buenas, saltos mayores penalizados
            if degree_diff == 0:
                scores.append(0.6)  # Unisono: aceptable
            elif degree_diff == 1:
                scores.append(1.0)  # Segunda: ideal
            elif degree_diff == 2:
                scores.append(0.85)  # Tercera: muy bueno
            elif degree_diff == 3:
                scores.append(0.7)  # Cuarta: bueno
            elif degree_diff == 4:
                scores.append(0.5)  # Quinta: aceptable
            elif degree_diff == 5:
                scores.append(0.3)  # Sexta: cuidado
            else:
                scores.append(0.1)  # Septima+: evitar

        return mean(scores) if scores else 0.5

    def _score_harmonic(self, chromosome: List[MotifGene]) -> float:
        """Evalua compatibilidad armonica."""
        chord_tones = self.context.harmony_manager.get_chord_tones_for_function(1)
        characteristic_degree = self.context.get_characteristic_degree()

        scores = []
        for i, gene in enumerate(chromosome):
            is_chord_tone = gene.degree in chord_tones
            is_characteristic = gene.degree == characteristic_degree

            # Primera nota: preferir nota del acorde
            if i == 0:
                if is_chord_tone:
                    scores.append(1.0)
                elif is_characteristic:
                    scores.append(0.9)  # Premiar nota caracteristica
                else:
                    scores.append(0.5)
            # Otras notas: mas flexibilidad
            else:
                if is_chord_tone:
                    scores.append(0.9)
                elif is_characteristic:
                    scores.append(0.85)  # Premiar nota caracteristica
                else:
                    scores.append(0.7)  # Notas de paso aceptables

        return mean(scores) if scores else 0.5

    def _score_contour(self, chromosome: List[MotifGene]) -> float:
        """Evalua calidad del contorno melodico."""
        if len(chromosome) < 3:
            return 0.7

        # Calcular direcciones
        directions = []
        for i in range(1, len(chromosome)):
            diff = chromosome[i].degree - chromosome[i - 1].degree
            if diff > 0:
                directions.append(1)
            elif diff < 0:
                directions.append(-1)
            else:
                directions.append(0)

        # Preferir contornos con forma (no monotonos)
        direction_changes = sum(
            1 for i in range(1, len(directions))
            if directions[i] != directions[i - 1] and directions[i] != 0
        )

        # Penalizar demasiados cambios (erratico) o ninguno (monotono)
        ideal_changes = len(directions) // 3
        change_score = 1.0 - abs(direction_changes - ideal_changes) * 0.15

        # Verificar que hay movimiento
        has_movement = any(d != 0 for d in directions)
        movement_score = 0.8 if has_movement else 0.3

        return max(0.2, min(1.0, (change_score + movement_score) / 2))

    def _score_rhythmic_interest(self, chromosome: List[MotifGene]) -> float:
        """Evalua interes ritmico (variedad sin caos)."""
        if len(chromosome) < 2:
            return 0.5

        # Contar duraciones unicas
        durations = [gene.duration_idx for gene in chromosome]
        unique_durations = len(set(durations))

        # Ideal: 2-3 duraciones diferentes en un motivo de 4-6 notas
        if unique_durations == 1:
            variety_score = 0.4  # Muy monotono
        elif unique_durations == 2:
            variety_score = 0.9  # Buen balance
        elif unique_durations == 3:
            variety_score = 1.0  # Ideal
        else:
            variety_score = 0.7  # Quizas demasiado variado

        # Verificar que no hay cambios muy abruptos
        stability_scores = []
        for i in range(1, len(durations)):
            diff = abs(durations[i] - durations[i - 1])
            if diff <= 1:
                stability_scores.append(1.0)
            elif diff <= 2:
                stability_scores.append(0.8)
            else:
                stability_scores.append(0.5)

        stability = mean(stability_scores) if stability_scores else 0.7

        return (variety_score + stability) / 2

    def _score_development_potential(self, chromosome: List[MotifGene]) -> float:
        """Evalua facilidad de variacion (desarrollo motivico)."""
        if len(chromosome) < 3:
            return 0.5

        # Un buen motivo tiene intervalos caracteristicos
        intervals = []
        for i in range(1, len(chromosome)):
            intervals.append(chromosome[i].degree - chromosome[i - 1].degree)

        # Preferir motivos con al menos un intervalo distintivo
        has_distinctive_interval = any(abs(i) >= 2 for i in intervals)

        # Preferir motivos que no sean simetricamente triviales
        is_trivial = all(i == intervals[0] for i in intervals) if intervals else True

        base_score = 0.7
        if has_distinctive_interval:
            base_score += 0.2
        if not is_trivial:
            base_score += 0.1

        return min(1.0, base_score)

    def _score_range(self, chromosome: List[MotifGene]) -> float:
        """Evalua rango melodico (preferir centro del ambito)."""
        if not chromosome:
            return 0.5

        scores = []
        for gene in chromosome:
            if self.context.is_in_range(gene):
                # Preferir octava central
                if gene.octave_offset == 0:
                    scores.append(1.0)
                else:
                    scores.append(0.7)
            else:
                scores.append(0.2)

        return mean(scores) if scores else 0.5


# ============================================================================
# OPERADORES GENETICOS
# ============================================================================

def create_random_gene() -> MotifGene:
    """Crea un gen aleatorio."""
    return MotifGene(
        degree=random.randint(1, 7),
        octave_offset=random.choice([-1, 0, 0, 0, 1]),  # Preferir octava central
        duration_idx=random.choice([1, 2, 3])  # Preferir corchea-negra
    )


def create_random_chromosome(length: int) -> List[MotifGene]:
    """Crea un cromosoma aleatorio de longitud especificada."""
    return [create_random_gene() for _ in range(length)]


def crossover_musical(
    parent1: List[MotifGene],
    parent2: List[MotifGene]
) -> Tuple[List[MotifGene], List[MotifGene]]:
    """
    Crossover que respeta estructura musical.
    Intercambia segmentos en puntos estructurales (inicio, mitad).
    """
    if len(parent1) < 2 or len(parent2) < 2:
        return [g.clone() for g in parent1], [g.clone() for g in parent2]

    # Puntos de corte en posiciones estructurales
    min_len = min(len(parent1), len(parent2))
    strong_points = [0, min_len // 2]
    point = random.choice(strong_points)

    if point == 0:
        point = min_len // 2

    # Crear hijos
    child1 = [g.clone() for g in parent1[:point]] + [g.clone() for g in parent2[point:min_len]]
    child2 = [g.clone() for g in parent2[:point]] + [g.clone() for g in parent1[point:min_len]]

    return child1, child2


def mutate_diatonic(chromosome: List[MotifGene], indpb: float = 0.2) -> Tuple[List[MotifGene]]:
    """
    Mutacion que mantiene diatonismo.
    Mueve grados por paso (+-1-2) dentro de escala.
    """
    for gene in chromosome:
        if random.random() < indpb:
            delta = random.choice([-2, -1, 1, 2])
            new_degree = gene.degree + delta
            # Normalizar a 1-7
            gene.degree = ((new_degree - 1) % 7) + 1

    return (chromosome,)


def mutate_rhythm(chromosome: List[MotifGene], indpb: float = 0.15) -> Tuple[List[MotifGene]]:
    """Mutacion de duracion a valor adyacente valido."""
    for gene in chromosome:
        if random.random() < indpb:
            delta = random.choice([-1, 1])
            gene.duration_idx = max(0, min(len(VALID_DURATIONS) - 1, gene.duration_idx + delta))

    return (chromosome,)


def mutate_octave(chromosome: List[MotifGene], indpb: float = 0.1) -> Tuple[List[MotifGene]]:
    """Mutacion de octava."""
    for gene in chromosome:
        if random.random() < indpb:
            delta = random.choice([-1, 1])
            gene.octave_offset = max(-1, min(1, gene.octave_offset + delta))

    return (chromosome,)


def mutate_transform(chromosome: List[MotifGene], indpb: float = 0.1) -> Tuple[List[MotifGene]]:
    """
    Aplica transformacion motivica completa (inversion, retrogradacion).
    """
    if random.random() < indpb and len(chromosome) >= 2:
        transform = random.choice(["inversion", "retrograde"])

        if transform == "inversion":
            # Invertir intervalos respecto al primer grado
            pivot = chromosome[0].degree
            for i in range(1, len(chromosome)):
                original_interval = chromosome[i].degree - pivot
                chromosome[i].degree = pivot - original_interval
                # Normalizar
                chromosome[i].degree = ((chromosome[i].degree - 1) % 7) + 1

        elif transform == "retrograde":
            # Invertir orden
            chromosome.reverse()

    return (chromosome,)


def mutate_combined(
    chromosome: List[MotifGene],
    diatonic_pb: float = 0.2,
    rhythm_pb: float = 0.15,
    octave_pb: float = 0.1,
    transform_pb: float = 0.05
) -> Tuple[List[MotifGene]]:
    """Aplica todas las mutaciones con probabilidades configurables."""
    mutate_diatonic(chromosome, diatonic_pb)
    mutate_rhythm(chromosome, rhythm_pb)
    mutate_octave(chromosome, octave_pb)
    mutate_transform(chromosome, transform_pb)
    return (chromosome,)


# ============================================================================
# EVOLUCIONADOR PRINCIPAL
# ============================================================================

class GeneticMelodyEvolver:
    """
    Evoluciona motivos melodicos usando algoritmos geneticos.

    Pipeline:
    1. Fase 1: Evolucionar motivo base (4-6 notas)
    2. Fase 2: Desarrollar a frase (variaciones del motivo)
    3. Fase 3: Desarrollar a periodo (antecedente + consecuente)
    """

    def __init__(
        self,
        scale_manager: ScaleManager,
        harmony_manager: HarmonyManager,
        config: Optional[GeneticConfig] = None,
    ):
        """
        Inicializa el evolucionador.

        Args:
            scale_manager: Gestor de escalas (define el modo)
            harmony_manager: Gestor de armonia
            config: Configuracion genetica (usa defaults si None)
        """
        self.config = config or GeneticConfig()
        self.context = GeneticContext(
            scale_manager=scale_manager,
            harmony_manager=harmony_manager,
            config=self.config,
        )
        self.evaluator = MotifFitnessEvaluator(self.context)

        # Setup de DEAP
        self._setup_deap()

        logger.info(
            f"GeneticMelodyEvolver inicializado: "
            f"modo={scale_manager.mode}, "
            f"generaciones={self.config.generations}, "
            f"poblacion={self.config.population_size}"
        )

    def _setup_deap(self):
        """Configura DEAP con operadores geneticos musicales."""
        # Evitar redefinicion si ya existe
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()

        # Generadores
        motif_len = random.randint(*self.config.motif_length)
        self.toolbox.register("individual", tools.initIterate,
                              creator.Individual,
                              lambda: create_random_chromosome(motif_len))
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)

        # Operadores
        self.toolbox.register("evaluate", self.evaluator.evaluate)
        self.toolbox.register("mate", crossover_musical)
        self.toolbox.register("mutate", mutate_combined)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def evolve_base_motif(self) -> List[MotifGene]:
        """
        Evoluciona un motivo base de 4-6 notas.

        Returns:
            Mejor cromosoma encontrado
        """
        logger.debug(f"Evolucionando motivo base...")

        # Crear poblacion inicial
        pop = self.toolbox.population(n=self.config.population_size)

        # Evaluar poblacion inicial
        for ind in pop:
            ind.fitness.values = self.toolbox.evaluate(ind)

        # Evolucionar
        for gen in range(self.config.generations):
            # Seleccion
            offspring = self.toolbox.select(pop, len(pop) - self.config.elitism)
            offspring = [self.toolbox.clone(ind) for ind in offspring]

            # Crossover
            for i in range(0, len(offspring) - 1, 2):
                if random.random() < self.config.crossover_prob:
                    child1, child2 = self.toolbox.mate(offspring[i], offspring[i + 1])
                    # Convertir listas a Individuals de DEAP
                    offspring[i] = creator.Individual(child1)
                    offspring[i + 1] = creator.Individual(child2)

            # Mutacion
            for i, ind in enumerate(offspring):
                if random.random() < self.config.mutation_prob:
                    mutated = self.toolbox.mutate(ind)
                    # mutate retorna tupla, el primer elemento es el individuo mutado
                    if isinstance(mutated, tuple):
                        offspring[i] = creator.Individual(mutated[0])
                    else:
                        offspring[i] = creator.Individual(mutated)

            # Evaluar nuevos individuos
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            for ind in invalid_ind:
                ind.fitness.values = self.toolbox.evaluate(ind)

            # Elitismo: mantener mejores
            elite = tools.selBest(pop, self.config.elitism)
            pop = elite + offspring

            # Log progreso
            if gen % 5 == 0:
                best_fitness = max(ind.fitness.values[0] for ind in pop)
                logger.debug(f"Generacion {gen}: mejor fitness = {best_fitness:.3f}")

        # Retornar mejor individuo
        best = tools.selBest(pop, 1)[0]
        logger.info(f"Motivo evolucionado: fitness = {best.fitness.values[0]:.3f}")

        return best

    def chromosome_to_motif(self, chromosome: List[MotifGene]) -> Motif:
        """
        Convierte un cromosoma a un objeto Motif.

        Args:
            chromosome: Lista de genes

        Returns:
            Motif con pitches, intervalos, ritmo y grados
        """
        pitches = []
        degrees = []
        intervals = []
        durations = []

        prev_pitch = None

        for gene in chromosome:
            # Obtener pitch
            pitch_str = self.context.gene_to_pitch(gene)
            pitches.append(pitch_str)
            degrees.append(gene.degree)

            # Calcular intervalo
            if prev_pitch is not None:
                curr_p = pitch.Pitch(pitch_str)
                prev_p = pitch.Pitch(prev_pitch)
                interval_semitones = int(curr_p.ps - prev_p.ps)
                intervals.append(interval_semitones)

            prev_pitch = pitch_str
            durations.append(gene.get_duration())

        rhythm = RhythmicPattern(
            durations=durations,
            strong_beat_indices=[0]
        )

        return Motif(
            pitches=pitches,
            intervals=intervals,
            rhythm=rhythm,
            degrees=degrees
        )

    def develop_motif_variation(
        self,
        base_chromosome: List[MotifGene],
        variation_type: MotivicVariation
    ) -> List[MotifGene]:
        """
        Desarrolla una variacion del motivo base.

        Args:
            base_chromosome: Cromosoma base
            variation_type: Tipo de variacion a aplicar

        Returns:
            Nuevo cromosoma con variacion aplicada
        """
        # Clonar cromosoma
        varied = [gene.clone() for gene in base_chromosome]

        if variation_type == MotivicVariation.ORIGINAL:
            return varied

        elif variation_type == MotivicVariation.RETROGRADE:
            varied.reverse()

        elif variation_type == MotivicVariation.INVERSION:
            if len(varied) >= 2:
                pivot = varied[0].degree
                for i in range(1, len(varied)):
                    original_interval = varied[i].degree - pivot
                    varied[i].degree = pivot - original_interval
                    varied[i].degree = ((varied[i].degree - 1) % 7) + 1

        elif variation_type == MotivicVariation.TRANSPOSITION:
            # Transponer por un intervalo aleatorio
            transpose = random.choice([2, 3, 4, 5])
            for gene in varied:
                gene.degree = ((gene.degree - 1 + transpose) % 7) + 1

        elif variation_type == MotivicVariation.AUGMENTATION:
            # Duplicar duraciones
            for gene in varied:
                gene.duration_idx = min(len(VALID_DURATIONS) - 1, gene.duration_idx + 1)

        elif variation_type == MotivicVariation.DIMINUTION:
            # Reducir duraciones
            for gene in varied:
                gene.duration_idx = max(0, gene.duration_idx - 1)

        return varied

    def develop_to_phrase(
        self,
        base_chromosome: List[MotifGene],
        num_variations: int = 3
    ) -> List[Motif]:
        """
        Desarrolla un motivo base en una frase (motivo + variaciones).

        Args:
            base_chromosome: Motivo base evolucionado
            num_variations: Numero de variaciones a generar

        Returns:
            Lista de Motifs que forman la frase
        """
        motifs = [self.chromosome_to_motif(base_chromosome)]

        # Seleccionar variaciones
        variation_types = [
            MotivicVariation.TRANSPOSITION,
            MotivicVariation.INVERSION,
            MotivicVariation.RETROGRADE,
            MotivicVariation.AUGMENTATION,
            MotivicVariation.DIMINUTION,
        ]

        for i in range(num_variations):
            var_type = random.choice(variation_types)
            varied_chromosome = self.develop_motif_variation(base_chromosome, var_type)
            motifs.append(self.chromosome_to_motif(varied_chromosome))

        return motifs

    def develop_to_period(
        self,
        base_chromosome: List[MotifGene],
        total_measures: int = 8
    ) -> Period:
        """
        Desarrolla un motivo base en un periodo completo.

        Args:
            base_chromosome: Motivo base evolucionado
            total_measures: Numero total de compases del periodo

        Returns:
            Period con antecedente y consecuente
        """
        base_motif = self.chromosome_to_motif(base_chromosome)

        # Antecedente: motivo + variacion, termina en V (semicadencia)
        antecedent_motifs = self.develop_to_phrase(base_chromosome, num_variations=1)

        # Consecuente: similar pero termina en I (cadencia autentica)
        # Usar variacion diferente para contraste
        consequent_variations = [
            MotivicVariation.TRANSPOSITION,
            MotivicVariation.INVERSION,
        ]

        consequent_motifs = [self.chromosome_to_motif(base_chromosome)]
        for var_type in consequent_variations[:1]:
            varied = self.develop_motif_variation(base_chromosome, var_type)
            consequent_motifs.append(self.chromosome_to_motif(varied))

        # Crear estructuras
        antecedent_phrases = []
        for i, motif in enumerate(antecedent_motifs):
            phrase = Phrase(
                motif=motif,
                variation=motif,  # Simplificado
                harmonic_progression=[
                    HarmonicFunction(degree=1, quality="major", tension=0.0, chord_tones=[1, 3, 5])
                ],
                measure_range=(i * 2, (i + 1) * 2),
                variation_type="genetic"
            )
            antecedent_phrases.append(phrase)

        consequent_phrases = []
        offset = len(antecedent_motifs) * 2
        for i, motif in enumerate(consequent_motifs):
            phrase = Phrase(
                motif=motif,
                variation=motif,
                harmonic_progression=[
                    HarmonicFunction(degree=5 if i == 0 else 1, quality="major", tension=0.5, chord_tones=[5, 7, 2])
                ],
                measure_range=(offset + i * 2, offset + (i + 1) * 2),
                variation_type="genetic"
            )
            consequent_phrases.append(phrase)

        antecedent = Semiphrase(
            phrases=antecedent_phrases,
            function="antecedent",
            cadence_type="half",
            measure_range=(0, total_measures // 2)
        )

        consequent = Semiphrase(
            phrases=consequent_phrases,
            function="consequent",
            cadence_type="authentic",
            measure_range=(total_measures // 2, total_measures)
        )

        # Plan armonico
        harmonic_plan = [
            HarmonicFunction(degree=1, quality="major", tension=0.0, chord_tones=[1, 3, 5]),
            HarmonicFunction(degree=4, quality="major", tension=0.3, chord_tones=[4, 6, 1]),
            HarmonicFunction(degree=5, quality="major", tension=0.7, chord_tones=[5, 7, 2]),
            HarmonicFunction(degree=1, quality="major", tension=0.0, chord_tones=[1, 3, 5]),
        ]

        return Period(
            antecedent=antecedent,
            consequent=consequent,
            total_measures=total_measures,
            base_motif=base_motif,
            harmonic_plan=harmonic_plan
        )

    def evolve_and_develop(self, total_measures: int = 8) -> Tuple[Period, List[MotifGene]]:
        """
        Pipeline completo: evoluciona motivo y lo desarrolla en periodo.

        Args:
            total_measures: Numero total de compases

        Returns:
            Tupla (Period, cromosoma_base)
        """
        # Fase 1: Evolucionar motivo base
        best_chromosome = self.evolve_base_motif()

        # Fase 2-3: Desarrollar a periodo
        period = self.develop_to_period(best_chromosome, total_measures)

        return period, best_chromosome
