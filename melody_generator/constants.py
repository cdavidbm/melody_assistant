"""
Constantes de teoría musical para el generador de melodías.

Este módulo centraliza los "números mágicos" utilizados en el sistema,
documentando la teoría musical detrás de cada valor. Esto facilita:
1. Entender el razonamiento detrás de cada decisión
2. Ajustar parámetros sistemáticamente
3. Mantener consistencia en todo el código

Referencias teóricas:
- Kostka & Payne: "Tonal Harmony" (conducción de voces)
- Krumhansl: "Cognitive Foundations of Musical Pitch" (perfiles de tonalidad)
- Lerdahl & Jackendoff: "A Generative Theory of Tonal Music" (estructura métrica)
"""

from typing import Dict, List, Tuple


# =============================================================================
# CONDUCCIÓN DE VOCES (Voice Leading)
# =============================================================================
# Basado en principios de escritura clásica: el movimiento por grados conjuntos
# (segundas) es preferido sobre saltos, y los saltos pequeños sobre los grandes.
# Esto crea líneas melódicas más fluidas y cantables.

VOICE_LEADING_SCORES: Dict[str, float] = {
    # Intervalo en semitonos -> Score (0.0 - 1.0)
    #
    # Unísono (0 semitonos): Aceptable pero estático
    # - No hay movimiento melódico
    # - Usado para repetición de notas importantes
    "unison": 0.6,

    # Segunda menor/mayor (1-2 semitonos): Movimiento ideal por grado conjunto
    # - Preferido en la escritura clásica
    # - Crea conexión suave entre notas
    "second": 1.0,

    # Tercera menor/mayor (3-4 semitonos): Buen salto melódico
    # - Muy común en melodías cantables
    # - Mantiene coherencia melódica
    "third": 0.85,

    # Cuarta justa (5 semitonos): Salto moderado
    # - Usado para énfasis o cambio de dirección
    # - Requiere resolución posterior por grado conjunto
    "fourth": 0.7,

    # Quinta justa (7 semitonos): Salto aceptable
    # - Común al inicio de frases (salto inicial)
    # - Generalmente compensado con movimiento contrario
    "fifth": 0.5,

    # Sexta menor/mayor (8-9 semitonos): Usar con precaución
    # - Salto expresivo, dramático
    # - Debe resolverse por grado conjunto en dirección opuesta
    "sixth": 0.3,

    # Séptima o mayor (10+ semitonos): Evitar
    # - Rompe la línea melódica
    # - Solo en casos muy específicos (saltos de octava)
    "seventh_plus": 0.1,
}

# Mapeo de semitonos a categorías
INTERVAL_TO_CATEGORY: Dict[int, str] = {
    0: "unison",
    1: "second", 2: "second",
    3: "third", 4: "third",
    5: "fourth",
    6: "fourth",  # Tritono tratado como cuarta aumentada
    7: "fifth",
    8: "sixth", 9: "sixth",
    10: "seventh_plus", 11: "seventh_plus", 12: "seventh_plus",
}

# Primera nota: score neutral-positivo (no hay contexto previo)
FIRST_NOTE_VOICE_LEADING_SCORE: float = 0.8


# =============================================================================
# ARMONÍA Y TIEMPOS FUERTES
# =============================================================================
# En la tradición clásica, las notas del acorde deben aparecer en tiempos fuertes
# mientras que las notas de paso/bordadura pueden aparecer en tiempos débiles.

HARMONIC_SCORES: Dict[str, Dict[str, float]] = {
    # Tiempo fuerte (downbeat, beat 1 y 3 en 4/4)
    "strong": {
        "chord_tone": 1.0,    # Nota del acorde: ideal
        "non_chord": 0.3,     # Nota de paso: evitar
    },

    # Tiempo semi-fuerte (beat 2 en 4/4)
    "semi_strong": {
        "chord_tone": 0.9,
        "non_chord": 0.5,
    },

    # Tiempo débil (subdivisiones, beats off)
    "weak": {
        "chord_tone": 0.8,
        "non_chord": 0.7,     # Notas de paso más aceptables
    },
}


# =============================================================================
# CONTORNO MELÓDICO
# =============================================================================
# Scores para adherencia al contorno planificado de la frase.
# Basado en el principio de que las melodías efectivas tienen forma direccional.

CONTOUR_SCORES: Dict[str, float] = {
    # Grado exacto al objetivo: perfecto
    "exact_match": 1.0,

    # 1 grado de diferencia: muy bueno
    "one_off": 0.8,

    # 2 grados de diferencia: aceptable
    "two_off": 0.6,

    # 3+ grados de diferencia: menos deseable
    "far_off": 0.4,

    # Sin objetivo definido: neutral
    "no_target": 0.5,
}


# =============================================================================
# NOTAS DE TENDENCIA
# =============================================================================
# En música tonal, ciertas notas tienen "tendencia" a resolver hacia otras:
# - 7 (sensible) -> 1 (tónica): Muy fuerte
# - 4 -> 3: Fuerte
# - 2 -> 1: Moderada
# - 6 -> 5: Suave

TENDENCY_TONES: Dict[int, Dict[str, any]] = {
    # Grado 7 (sensible): debe resolver a grado 1
    7: {
        "resolves_to": 1,
        "strength": 0.9,        # Fuerza de la tendencia
        "reward": 1.0,          # Score si resuelve correctamente
        "penalty": 0.2,         # Score si no resuelve
    },

    # Grado 4: tiende a resolver a grado 3
    4: {
        "resolves_to": 3,
        "strength": 0.7,
        "reward": 0.9,
        "penalty": 0.4,
    },

    # Grado 2: puede resolver a grado 1
    2: {
        "resolves_to": 1,
        "strength": 0.5,
        "reward": 0.85,
        "penalty": 0.5,
    },

    # Grado 6: puede resolver a grado 5
    6: {
        "resolves_to": 5,
        "strength": 0.4,
        "reward": 0.8,
        "penalty": 0.6,
    },
}

# Score cuando no hay tendencia pendiente
NO_TENDENCY_SCORE: float = 0.7


# =============================================================================
# VARIEDAD Y REPETICIÓN
# =============================================================================
# Evitar repetición excesiva de notas para mantener interés melódico.

VARIETY_SCORES: Dict[str, float] = {
    # Primera aparición de una nota: neutral
    "first_appearance": 0.8,

    # Segunda aparición reciente (últimas 4 notas): penalizar levemente
    "recent_repeat": 0.5,

    # Nota muy repetida: penalizar más
    "over_repeated": 0.3,
}

# Ventana de notas recientes para verificar repetición
RECENT_NOTES_WINDOW: int = 4


# =============================================================================
# RANGO MELÓDICO
# =============================================================================
# Preferencia por el centro del rango vocal para melodías cantables.

RANGE_CONFIG: Dict[str, any] = {
    # Rango vocal típico (MIDI notes)
    "min_midi": 48,          # C3 - Límite bajo cómodo
    "max_midi": 84,          # C6 - Límite alto cómodo
    "center_midi": 66,       # F#4 - Centro del rango

    # Scores por posición en el rango
    "center_score": 1.0,     # En el centro: ideal
    "edge_score": 0.6,       # En los extremos: menos ideal

    # Máximo ámbito recomendado (en semitonos)
    "max_ambitus": 24,       # 2 octavas
}


# =============================================================================
# PESOS DEL SISTEMA DE SCORING
# =============================================================================
# Pesos por defecto para cada criterio de puntuación.
# Sumados = 100% (1.0)
#
# Estos pesos reflejan la importancia relativa de cada aspecto en la
# composición clásica:

DEFAULT_SCORING_WEIGHTS: Dict[str, float] = {
    # Voice leading: Lo más importante para líneas melódicas fluidas
    "voice_leading": 0.28,

    # Harmonic: Notas del acorde en tiempos fuertes
    "harmonic": 0.22,

    # Contour: Seguir la forma planificada de la frase
    "contour": 0.15,

    # Tendency: Resolver notas de tendencia correctamente
    "tendency": 0.12,

    # Markov: Patrones aprendidos de compositores (si está habilitado)
    "markov": 0.10,

    # Variety: Evitar repetición excesiva
    "variety": 0.08,

    # Range: Preferir centro del rango vocal
    "range": 0.05,
}


# =============================================================================
# SUBDIVISIÓN RÍTMICA
# =============================================================================
# Probabilidades de diferentes patrones rítmicos según complejidad y posición.
#
# La música clásica tiende a usar valores más largos en tiempos fuertes
# y subdivisiones más cortas en tiempos débiles.

RHYTHM_PROBABILITIES: Dict[str, Dict[str, float]] = {
    # Complejidad 1 (Simple): Principalmente negras
    "complexity_1": {
        "strong_beat_quarter": 1.0,      # 100% negras en tiempo fuerte
        "weak_beat_quarter": 0.7,        # 70% negras, 30% dos corcheas
    },

    # Complejidad 2 (Moderada): Más variación
    "complexity_2": {
        "strong_beat_quarter": 0.8,      # 80% negras en tiempo fuerte
        "weak_beat_quarter": 0.4,        # 40% negras
        "weak_beat_eighths": 0.4,        # 40% dos corcheas
        "weak_beat_dotted": 0.2,         # 20% puntillo + semicorchea
    },

    # Complejidad 3+ (Compleja): Máxima variación
    "complexity_3": {
        "strong_beat_quarter": 0.7,
        "weak_beat_quarter": 0.3,
        "weak_beat_eighths": 0.2,
        "weak_beat_dotted": 0.2,
        "weak_beat_sixteenths": 0.3,     # 30% cuatro semicorcheas
    },
}


# =============================================================================
# CADENCIAS
# =============================================================================
# Tipos de cadencias y sus características.

CADENCE_CONFIG: Dict[str, Dict[str, any]] = {
    "authentic_perfect": {
        "final_degree": 1,       # Termina en tónica
        "penultimate_degree": 7, # Sensible antes
        "strength": 1.0,         # Muy conclusiva
    },
    "authentic_imperfect": {
        "final_degree": 1,
        "penultimate_degree": 2, # Grado 2 antes
        "strength": 0.8,
    },
    "half": {
        "final_degree": 5,       # Termina en dominante
        "strength": 0.5,         # Suspensiva
    },
    "deceptive": {
        "final_degree": 6,       # Termina en VI (engañosa)
        "strength": 0.6,
    },
    "plagal": {
        "final_degree": 1,
        "penultimate_degree": 4, # IV -> I
        "strength": 0.7,
    },
}


# =============================================================================
# CONTORNO DE FRASE
# =============================================================================
# Configuración de contornos típicos para frases antecedentes y consecuentes.

PHRASE_CONTOUR_CONFIG: Dict[str, Dict[str, float]] = {
    # Frase antecedente: sube hacia clímax, termina en dominante (abierta)
    "antecedent": {
        "climax_position": 0.6,  # Clímax al 60% de la frase
        "start_degree": 1,       # Comienza en tónica
        "end_degree": 5,         # Termina en dominante
    },

    # Frase consecuente: clímax más temprano, termina en tónica (cerrada)
    "consequent": {
        "climax_position": 0.5,  # Clímax al 50%
        "start_degree": 1,
        "end_degree": 1,         # Termina en tónica
    },
}


# =============================================================================
# VALIDACIÓN
# =============================================================================
# Umbrales para el sistema de validación.

VALIDATION_THRESHOLDS: Dict[str, float] = {
    # Score mínimo para considerar válido
    "target_score": 0.80,

    # Máximo de rondas de corrección
    "max_correction_rounds": 5,

    # Mejora mínima para continuar corrigiendo
    "min_improvement": 0.02,

    # Porcentaje mínimo de notas diatónicas
    "min_diatonic_percentage": 0.75,

    # Correlación mínima para detección de tonalidad
    "min_key_correlation": 0.70,
}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def get_voice_leading_score(semitones: int) -> float:
    """
    Obtiene el score de voice leading para un intervalo dado.

    Args:
        semitones: Tamaño del intervalo en semitonos (valor absoluto)

    Returns:
        Score entre 0.0 y 1.0
    """
    semitones = abs(semitones)

    if semitones > 12:
        return VOICE_LEADING_SCORES["seventh_plus"]

    category = INTERVAL_TO_CATEGORY.get(semitones, "seventh_plus")
    return VOICE_LEADING_SCORES.get(category, 0.1)


def get_rhythm_probability(complexity: int, beat_type: str) -> float:
    """
    Obtiene la probabilidad para un tipo de subdivisión rítmica.

    Args:
        complexity: Nivel de complejidad rítmica (1-3)
        beat_type: Tipo de subdivisión ("strong_beat_quarter", etc.)

    Returns:
        Probabilidad entre 0.0 y 1.0
    """
    complexity = max(1, min(3, complexity))
    key = f"complexity_{complexity}"

    probs = RHYTHM_PROBABILITIES.get(key, RHYTHM_PROBABILITIES["complexity_2"])
    return probs.get(beat_type, 0.5)
