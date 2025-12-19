"""
Interfaz de línea de comandos para el generador de melodías.
Dividido en funciones para mejor organización (SRP).
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import abjad

from .models import ImpulseType
from .config import (
    GenerationConfig,
    TonalConfig,
    MeterConfig,
    RhythmConfig,
    MelodyConfig,
    MotifConfig,
    MarkovConfig,
    ValidationConfig,
    OutputConfig,
    ExpressionConfig,
)
from .architect import MelodicArchitect
from .bass import BassStyle, BassConfig
from .validation import MusicValidator, ValidationReport, AutoCorrector


# Mapeo de estilos de ornamentación
ORNAMENTATION_STYLE_MAP = {
    "1": "baroque",
    "2": "classical",
    "3": "romantic",
    "4": "minimal",
    "5": "none",
}


# Mapeo de selección de modo
MODE_MAP = {
    # Diatónicos
    "1": "major",
    "2": "dorian",
    "3": "phrygian",
    "4": "lydian",
    "5": "mixolydian",
    "6": "minor",
    "7": "locrian",
    # Menores
    "8": "harmonic_minor",
    "9": "melodic_minor",
    # Menor armónica
    "10": "locrian_nat6",
    "11": "ionian_aug5",
    "12": "dorian_sharp4",
    "13": "phrygian_dominant",
    "14": "lydian_sharp2",
    "15": "superlocrian_bb7",
    # Menor melódica
    "16": "dorian_flat2",
    "17": "lydian_augmented",
    "18": "lydian_dominant",
    "19": "mixolydian_flat6",
    "20": "locrian_nat2",
    "21": "altered",
}

# Mapeo de compositores para Markov
COMPOSER_MAP = {
    "1": "bach",
    "2": "mozart",
    "3": "beethoven",
    "4": "combined",
}

# Mapeo de niveles de tolerancia
TOLERANCE_MAP = {
    "1": 0.85,  # Estricto
    "2": 0.65,  # Moderado
    "3": 0.45,  # Permisivo
}

# Mapeo de estilos de bajo
BASS_STYLE_MAP = {
    "1": "simple",
    "2": "alberti",
    "3": "walking",
    "4": "contrapunto",
}


def print_header():
    """Imprime el encabezado del programa."""
    print("=" * 70)
    print("GENERADOR DE MELODÍAS - PROTOCOLO SYMMETRY & LOGIC")
    print("=" * 70)
    print()
    print("Este programa genera melodías basadas en teoría musical clásica.")
    print()


def print_mode_menu():
    """Imprime el menú de selección de modos."""
    print("\nModos disponibles:")
    print("\n--- MODOS DIATÓNICOS (de escala mayor) ---")
    print("1. major (Jónico / Mayor)")
    print("2. dorian (Dórico)")
    print("3. phrygian (Frigio)")
    print("4. lydian (Lidio)")
    print("5. mixolydian (Mixolidio)")
    print("6. minor (Aeolian / Menor natural)")
    print("7. locrian (Locrio)")

    print("\n--- ESCALAS MENORES ---")
    print("8. harmonic_minor (Menor armónica)")
    print("9. melodic_minor (Menor melódica)")

    print("\n--- MODOS DE MENOR ARMÓNICA ---")
    print("10. locrian_nat6 (Locrio ♮6)")
    print("11. ionian_aug5 (Jónico aumentado)")
    print("12. dorian_sharp4 (Dórico #4 / Ucraniano)")
    print("13. phrygian_dominant (Frigio dominante / Frigio mayor)")
    print("14. lydian_sharp2 (Lidio #2)")
    print("15. superlocrian_bb7 (Ultralocrio)")

    print("\n--- MODOS DE MENOR MELÓDICA ---")
    print("16. dorian_flat2 (Dórico ♭2 / Frigio #6)")
    print("17. lydian_augmented (Lidio aumentado)")
    print("18. lydian_dominant (Lidio dominante / Mixolidio #4)")
    print("19. mixolydian_flat6 (Mixolidio ♭6)")
    print("20. locrian_nat2 (Locrio ♮2 / Semilocrio)")
    print("21. altered (Alterado / Superlocrio)")


def get_tonal_config() -> TonalConfig:
    """Obtiene la configuración tonal del usuario."""
    key_name = input("Tonalidad (ej: C, D, Eb, F#) [C]: ").strip() or "C"

    print_mode_menu()
    mode_choice = input("\nSeleccione modo [1]: ").strip() or "1"
    mode = MODE_MAP.get(mode_choice, "major")

    return TonalConfig(key_name=key_name, mode=mode)


def get_meter_config() -> MeterConfig:
    """Obtiene la configuración de métrica del usuario."""
    print("\nCompás:")
    numerator = int(input("  Numerador (pulsos por compás) [4]: ").strip() or "4")
    denominator = int(input("  Denominador (figura que cuenta) [4]: ").strip() or "4")
    meter_tuple = (numerator, denominator)

    subdivisions = None
    if numerator in [5, 7, 11]:
        print(f"\nMétrica amalgama detectada ({numerator}/{denominator})")
        print(f"¿Cómo subdividir los {numerator} pulsos?")
        subdivisions = _parse_subdivisions(numerator)

    num_measures = int(input("\nNúmero de compases [8]: ").strip() or "8")

    return MeterConfig(
        meter_tuple=meter_tuple,
        subdivisions=subdivisions,
        num_measures=num_measures,
    )


def _parse_subdivisions(numerator: int) -> list:
    """Parsea las subdivisiones para métricas amalgama."""
    if numerator == 5:
        subdiv_input = input("  Ej: 2+3 o 3+2 [2+3]: ").strip() or "2+3"
    elif numerator == 7:
        subdiv_input = input("  Ej: 2+2+3 o 3+2+2 [2+2+3]: ").strip() or "2+2+3"
    else:
        subdiv_input = input(f"  Separados por + (deben sumar {numerator}): ").strip()

    return [int(x) for x in subdiv_input.split("+")]


def get_rhythm_config() -> RhythmConfig:
    """Obtiene la configuración rítmica del usuario."""
    print("\nComplejidad rítmica:")
    print("1. Simple (negras y corcheas)")
    print("2. Moderado (incluye puntillos)")
    print("3. Complejo (semicorcheas y subdivisiones)")
    complexity = int(input("Seleccione [2]: ").strip() or "2")

    use_rests_input = (
        input("\n¿Usar silencios como respiraciones? (s/n) [s]: ").strip().lower()
        or "s"
    )
    use_rests = use_rests_input == "s"

    return RhythmConfig(
        complexity=complexity,
        use_rests=use_rests,
        rest_probability=0.15,
    )


def get_melody_config() -> MelodyConfig:
    """Obtiene la configuración melódica del usuario."""
    print("\nTipo de impulso:")
    print("1. Tético (comienza en tiempo fuerte)")
    print("2. Anacrúsico (comienza antes del tiempo fuerte)")
    print("3. Acéfalo (comienza después del tiempo fuerte)")
    impulse_choice = input("Seleccione [1]: ").strip() or "1"
    impulse_map = {
        "1": ImpulseType.TETIC,
        "2": ImpulseType.ANACROUSTIC,
        "3": ImpulseType.ACEPHALOUS,
    }
    impulse_type = impulse_map.get(impulse_choice, ImpulseType.TETIC)

    use_tenoris_input = (
        input("\n¿Usar 'tenoris' (quinta como nota sostenedora)? (s/n) [n]: ")
        .strip()
        .lower()
        or "n"
    )
    use_tenoris = use_tenoris_input == "s"

    climax_input = input("\nPosición del clímax (0.0-1.0) [0.75]: ").strip()
    climax_pos = float(climax_input) if climax_input else 0.75

    return MelodyConfig(
        impulse_type=impulse_type,
        climax_position=climax_pos,
        climax_intensity=1.5,
        max_interval=6,
        infraction_rate=0.1,
        use_tenoris=use_tenoris,
        tenoris_probability=0.2,
    )


def get_motif_config() -> MotifConfig:
    """Obtiene la configuración de motivos del usuario."""
    print("\nLibertad de variación motívica:")
    print("1. Estricta (motivo muy reconocible, variaciones conservadoras)")
    print("2. Moderada (equilibrio entre familiaridad y novedad)")
    print("3. Libre (máxima libertad creativa)")
    variation_freedom_input = input("Seleccione nivel [2]: ").strip() or "2"
    variation_freedom = (
        int(variation_freedom_input)
        if variation_freedom_input in ["1", "2", "3"]
        else 2
    )

    return MotifConfig(
        use_motivic_variations=True,
        variation_probability=0.4,
        variation_freedom=variation_freedom,
    )


def get_markov_config() -> MarkovConfig:
    """Obtiene la configuración de Markov del usuario."""
    print("\n=== CADENAS DE MARKOV (Aprendizaje de Compositores Clásicos) ===")
    print()
    print("Las cadenas de Markov permiten que el generador aprenda patrones")
    print("melódicos y rítmicos de compositores clásicos del corpus de music21.")
    print()

    use_markov_input = (
        input("¿Usar cadenas de Markov? (s/n) [n]: ").strip().lower() or "n"
    )
    use_markov = use_markov_input == "s"

    if not use_markov:
        return MarkovConfig(enabled=False)

    print("\nCompositor de referencia:")
    print("1. Bach (363 obras - estilo contrapuntístico)")
    print("2. Mozart (11 obras - estilo clásico elegante)")
    print("3. Beethoven (23 obras - estilo dramático)")
    print("4. Combinado (mezcla de los tres estilos)")
    composer_choice = input("Seleccione compositor [1]: ").strip() or "1"
    composer = COMPOSER_MAP.get(composer_choice, "bach")

    print("\nPeso de Markov (influencia en la generación):")
    print("  0.0 = No influye (solo reglas teóricas)")
    print("  0.5 = Balance equilibrado (recomendado)")
    print("  1.0 = Máxima influencia de Markov")
    weight_input = input("Peso de Markov (0.0-1.0) [0.5]: ").strip()
    weight = 0.5
    if weight_input:
        try:
            weight = max(0.0, min(1.0, float(weight_input)))
        except ValueError:
            pass

    print("\nOrden de la cadena (contexto previo):")
    print("  1 = Solo intervalo/ritmo previo (menos contexto)")
    print("  2 = Dos pasos previos (recomendado)")
    print("  3 = Tres pasos previos (máximo contexto)")
    order_input = input("Orden [2]: ").strip()
    order = int(order_input) if order_input in ["1", "2", "3"] else 2

    return MarkovConfig(
        enabled=True,
        composer=composer,
        weight=weight,
        order=order,
    )


def get_validation_tolerance() -> float:
    """Obtiene el nivel de tolerancia de validación."""
    print("\n=== VALIDACIÓN MUSICAL ===")
    print()
    print("El sistema validará automáticamente que la melodía generada")
    print("cumpla con las especificaciones de tonalidad, métrica y rango.")
    print()
    print("Nivel de exigencia en validación:")
    print("1. Estricto (80-90% de precisión)")
    print("2. Moderado (60-70% de precisión) [Recomendado]")
    print("3. Permisivo (40-50% de precisión)")

    tolerance_choice = input("Seleccione nivel [2]: ").strip() or "2"
    return TOLERANCE_MAP.get(tolerance_choice, 0.65)


def get_generation_method() -> str:
    """Pregunta al usuario el método de generación."""
    print("\nMétodo de generación:")
    print("1. Tradicional (sistema actual, cohesión rítmica)")
    print("2. Jerárquico (Motivo → Frase → Semifrase → Período)")
    print("3. Genético (Evolución de motivos con DEAP)")
    generation_method_input = input("Seleccione método [1]: ").strip() or "1"

    method_map = {
        "1": "traditional",
        "2": "hierarchical",
        "3": "genetic",
    }
    return method_map.get(generation_method_input, "traditional")


def get_bass_config() -> Optional[tuple]:
    """
    Pregunta si añadir bajo y obtiene la configuración.

    Returns:
        Tupla (bass_style, bass_config) o None si no quiere bajo
    """
    print("\n=== BAJO ARMÓNICO (Opcional) ===")
    print()
    print("El bajo proporciona fundamento armónico a la melodía,")
    print("creando una textura de dos voces (contrapunto básico).")
    print()

    add_bass_input = (
        input("¿Agregar línea de bajo? (s/n) [n]: ").strip().lower() or "n"
    )
    if add_bass_input != "s":
        return None

    print()
    print("Estilo de bajo:")
    print("1. Simple (una nota por compás - solemne, lento)")
    print("2. Alberti (arpegio: raíz-quinta-tercera-quinta - clásico)")
    print("3. Walking (movimiento diatónico por grados - más móvil)")
    print("4. Contrapunto (línea melódica independiente - polifónico)")
    bass_style_input = input("Seleccione estilo [1]: ").strip() or "1"
    bass_style_str = BASS_STYLE_MAP.get(bass_style_input, "simple")

    style_map = {
        "simple": BassStyle.SIMPLE,
        "alberti": BassStyle.ALBERTI,
        "walking": BassStyle.WALKING,
        "contrapunto": BassStyle.CONTRAPUNTO,
    }
    bass_style = style_map.get(bass_style_str, BassStyle.SIMPLE)

    print("\nOctava del bajo:")
    print("  2 = Muy grave (C2)")
    print("  3 = Grave (C3) [Recomendado]")
    print("  4 = Media (C4)")
    octave_input = input("Octava [3]: ").strip() or "3"
    try:
        octave = max(1, min(5, int(octave_input)))
    except ValueError:
        octave = 3

    print("\nPreferencia de nota del acorde:")
    print("La nota del bajo puede ser raíz, tercera o quinta del acorde.")
    print("(Por defecto: 70% raíz, 20% quinta, 10% tercera)")

    use_default = input("¿Usar preferencias por defecto? (s/n) [s]: ").strip().lower() or "s"

    if use_default == "s":
        bass_config = BassConfig(
            style=bass_style,
            octave=octave,
        )
    else:
        root_pref_input = input("Preferencia de raíz (0.0-1.0) [0.70]: ").strip() or "0.70"
        fifth_pref_input = input("Preferencia de quinta (0.0-1.0) [0.20]: ").strip() or "0.20"

        try:
            root_pref = float(root_pref_input)
            fifth_pref = float(fifth_pref_input)
            third_pref = max(0, 1.0 - root_pref - fifth_pref)
        except ValueError:
            root_pref, fifth_pref, third_pref = 0.70, 0.20, 0.10

        bass_config = BassConfig(
            style=bass_style,
            octave=octave,
            root_preference=root_pref,
            fifth_preference=fifth_pref,
            third_preference=third_pref,
        )

    print(f"\n✓ Configuración: {bass_style_str}, octava {octave}")

    return bass_style, bass_config


def get_genetic_config() -> dict:
    """Obtiene la configuración de algoritmos genéticos del usuario."""
    print("\n=== CONFIGURACIÓN DE ALGORITMOS GENÉTICOS ===")
    print()
    print("Los algoritmos genéticos evolucionan motivos musicales")
    print("optimizando múltiples criterios teóricos (voice leading,")
    print("armonía, contorno, ritmo, potencial de desarrollo).")
    print()

    # Generaciones
    print("Número de generaciones (más = más optimización, más lento):")
    print("  10 = Rápido (~300ms)")
    print("  15 = Equilibrado (~500ms) [Recomendado]")
    print("  30 = Exhaustivo (~1s)")
    gen_input = input("Generaciones [15]: ").strip() or "15"
    try:
        generations = max(5, min(100, int(gen_input)))
    except ValueError:
        generations = 15

    # Población
    print("\nTamaño de población (más = más diversidad):")
    print("  20 = Pequeña")
    print("  30 = Media [Recomendado]")
    print("  50 = Grande")
    pop_input = input("Población [30]: ").strip() or "30"
    try:
        population_size = max(10, min(200, int(pop_input)))
    except ValueError:
        population_size = 30

    # Pulido Markov
    print("\n¿Aplicar pulido Markov al resultado genético?")
    print("(Suaviza voice leading usando patrones aprendidos)")
    markov_polish_input = input("Pulido Markov (s/n) [s]: ").strip().lower() or "s"
    use_markov_polish = markov_polish_input == "s"

    return {
        "generations": generations,
        "population_size": population_size,
        "use_markov_polish": use_markov_polish,
    }


def get_expression_config() -> ExpressionConfig:
    """Obtiene la configuración de expresión musical del usuario."""
    print("\n=== CARACTERÍSTICAS EXPRESIVAS ===")
    print()
    print("Estas características añaden ornamentos, dinámicas y articulaciones")
    print("a la melodía generada para mayor musicalidad.")
    print()

    # Ornamentación
    print("Estilo de ornamentación:")
    print("1. Barroco (muchos ornamentos: trinos, mordentes, appoggiaturas)")
    print("2. Clásico (ornamentos moderados)")
    print("3. Romántico (expresivo, notas de paso cromáticas)")
    print("4. Mínimo (solo ornamentos esenciales)")
    print("5. Ninguno (sin ornamentos)")
    orn_choice = input("Seleccione estilo [5]: ").strip() or "5"
    orn_style = ORNAMENTATION_STYLE_MAP.get(orn_choice, "none")
    use_ornamentation = orn_style != "none"

    # Dinámicas
    use_dynamics_input = (
        input("\n¿Añadir dinámicas automáticas (p, f, cresc, dim)? (s/n) [s]: ")
        .strip()
        .lower()
        or "s"
    )
    use_dynamics = use_dynamics_input == "s"

    base_dynamic = "mf"
    climax_dynamic = "f"
    if use_dynamics:
        print("\nDinámica base:")
        print("1. pp (pianissimo)")
        print("2. p (piano)")
        print("3. mp (mezzo piano)")
        print("4. mf (mezzo forte) [Recomendado]")
        print("5. f (forte)")
        dyn_choice = input("Seleccione [4]: ").strip() or "4"
        dyn_map = {"1": "pp", "2": "p", "3": "mp", "4": "mf", "5": "f"}
        base_dynamic = dyn_map.get(dyn_choice, "mf")

        print("\nDinámica del clímax:")
        print("1. mf (mezzo forte)")
        print("2. f (forte) [Recomendado]")
        print("3. ff (fortissimo)")
        climax_choice = input("Seleccione [2]: ").strip() or "2"
        climax_map = {"1": "mf", "2": "f", "3": "ff"}
        climax_dynamic = climax_map.get(climax_choice, "f")

    # Articulaciones
    use_articulations_input = (
        input("\n¿Añadir articulaciones (staccato, legato, acentos)? (s/n) [s]: ")
        .strip()
        .lower()
        or "s"
    )
    use_articulations = use_articulations_input == "s"

    return ExpressionConfig(
        use_ornamentation=use_ornamentation,
        ornamentation_style=orn_style,
        use_dynamics=use_dynamics,
        base_dynamic=base_dynamic,
        climax_dynamic=climax_dynamic,
        use_articulations=use_articulations,
        articulation_style=orn_style if orn_style != "none" else "classical",
    )


def get_output_config() -> OutputConfig:
    """Obtiene la configuración de salida del usuario."""
    print("\n=== INFORMACIÓN DE LA PARTITURA ===")
    title = input("Título [Melodía Generada]: ").strip() or "Melodía Generada"
    composer = (
        input("Compositor [MelodicArchitect AI]: ").strip() or "MelodicArchitect AI"
    )

    return OutputConfig(
        title=title,
        composer=composer,
        auto_save=True,
        output_dir="output",
    )


def run_generation_loop(
    config: GenerationConfig,
    tolerance: float,
    generation_method: str = "traditional",
    expression_config: Optional[ExpressionConfig] = None,
    genetic_params: Optional[dict] = None,
    bass_params: Optional[dict] = None,
) -> Tuple[Optional[abjad.Staff], Optional[ValidationReport], Optional[str]]:
    """
    Ejecuta el ciclo de generación con validación.

    Args:
        config: Configuración de generación
        tolerance: Tolerancia de validación
        generation_method: "traditional", "hierarchical", o "genetic"
        expression_config: Configuración de expresión
        genetic_params: Parámetros genéticos si method="genetic"
        bass_params: Parámetros de bajo (opcional, se puede combinar con cualquier método)

    Returns:
        Tupla (staff, validation_report, lilypond_code) o (None, None, None) si se cancela
        lilypond_code se devuelve si hay bass_params
    """
    print("\n" + "=" * 70)
    print("Generando melodía con validación automática...")
    print("=" * 70)
    print()

    architect = MelodicArchitect(config=config, expression_config=expression_config)
    current_config = config
    current_expression = expression_config

    staff = None
    validation_report = None
    lilypond_code = None  # Solo para generación con bajo
    attempt = 0

    while True:
        attempt += 1
        print(f"\n{'─' * 70}")
        print(f"Intento {attempt}")
        print(f"{'─' * 70}\n")

        # Generar melodía
        has_expression = current_expression is not None and (
            current_expression.use_dynamics or
            current_expression.use_articulations or
            current_expression.use_ornamentation
        )

        # Paso 1: Generar melodía con el método elegido
        if generation_method == "genetic":
            print("Generando con método GENÉTICO (evolucionando motivos)...")
            gen_params = genetic_params or {}
            staff = architect.generate_period_genetic(
                generations=gen_params.get("generations", 15),
                population_size=gen_params.get("population_size", 30),
                use_markov_polish=gen_params.get("use_markov_polish", True),
            )
        elif generation_method == "hierarchical":
            print("Generando con método JERÁRQUICO...")
            result = architect.generate_period_hierarchical()
            staff = result[0] if isinstance(result, tuple) else result
        else:
            print("Generando con método TRADICIONAL...")
            staff = architect.generate_period()

        # Paso 2: Añadir bajo si está configurado
        if bass_params is not None:
            print("Añadiendo BAJO ARMÓNICO...")
            bass_prms = bass_params
            bass_style = bass_prms.get("bass_style", BassStyle.SIMPLE)
            bass_cfg = bass_prms.get("bass_config", None)

            # Generar melodía con bajo (usa la misma semilla armónica)
            lilypond_code = architect.generate_period_with_bass(
                bass_style=bass_style,
                bass_config=bass_cfg,
                return_staffs=False,
            )
            print("  ✓ Bajo generado con verificación de conducción de voces")

        # Aplicar características expresivas si están habilitadas
        if has_expression:
            print("Aplicando características expresivas...")
            staff = architect.apply_expression(staff)

        # Validar melodía
        print("Validando melodía generada...\n")
        validator = MusicValidator(
            staff=staff,
            lilypond_formatter=architect.lilypond_formatter,
            expected_key=config.tonal.key_name,
            expected_mode=config.tonal.mode,
            expected_meter=config.meter.meter_tuple,
            tolerance=tolerance,
        )

        validation_report = validator.validate_all()
        print(validation_report.format_detailed_report())
        print()

        if validation_report.is_valid:
            print(f"✓ Validación exitosa en intento {attempt}")
            break

        print(
            f"⚠️  Validación no superada (puntuación: {validation_report.overall_score:.1%})"
        )

        # Mostrar correcciones sugeridas
        auto_corrector = AutoCorrector(validation_report)
        print(f"\n{auto_corrector.get_correction_summary()}")

        # Preguntar al usuario
        print(f"\n{'─' * 70}")
        print("Opciones:")
        print("  1. Aplicar correcciones e intentar de nuevo")
        print("  2. Aceptar melodía actual (aunque no sea válida)")
        print("  3. Cancelar y salir")

        choice = input("\nSeleccione opción [1]: ").strip() or "1"

        if choice == "1":
            print("\n🔧 Aplicando correcciones automáticas...")
            # Aplicar correcciones
            corrected_params = auto_corrector.apply_to_architect_params({
                "key_name": current_config.tonal.key_name,
                "mode": current_config.tonal.mode,
                "rhythmic_complexity": current_config.rhythm.complexity,
                "max_interval": current_config.melody.max_interval,
                "infraction_rate": current_config.melody.infraction_rate,
            })

            # Actualizar config
            current_config = GenerationConfig.from_simple_params(
                key_name=corrected_params.get("key_name", config.tonal.key_name),
                mode=corrected_params.get("mode", config.tonal.mode),
                meter_tuple=config.meter.meter_tuple,
                subdivisions=config.meter.subdivisions,
                num_measures=config.meter.num_measures,
                impulse_type=config.melody.impulse_type,
                infraction_rate=corrected_params.get("infraction_rate", config.melody.infraction_rate),
                rhythmic_complexity=corrected_params.get("rhythmic_complexity", config.rhythm.complexity),
                use_rests=config.rhythm.use_rests,
                rest_probability=config.rhythm.rest_probability,
                use_motivic_variations=config.motif.use_motivic_variations,
                variation_probability=config.motif.variation_probability,
                climax_position=config.melody.climax_position,
                climax_intensity=config.melody.climax_intensity,
                max_interval=corrected_params.get("max_interval", config.melody.max_interval),
                use_tenoris=config.melody.use_tenoris,
                tenoris_probability=config.melody.tenoris_probability,
                variation_freedom=config.motif.variation_freedom,
                use_markov=config.markov.enabled,
                markov_composer=config.markov.composer,
                markov_weight=config.markov.weight,
                markov_order=config.markov.order,
            )

            architect = MelodicArchitect(config=current_config, expression_config=current_expression)
            print("\n🔄 Regenerando con parámetros corregidos...")

        elif choice == "2":
            print("\n⚠️  Aceptando melodía no validada...")
            break

        else:
            print("\n❌ Generación cancelada.")
            return None, None, None

    return staff, validation_report, lilypond_code


def save_output(
    lilypond_code: str,
    output_config: OutputConfig,
    tonal_config: TonalConfig,
):
    """Guarda la melodía generada."""
    # Auto-save
    output_dir = Path(output_config.output_dir)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    auto_filename = f"melody_{tonal_config.key_name}_{tonal_config.mode}_{timestamp}.ly"
    auto_filepath = output_dir / auto_filename

    try:
        with open(auto_filepath, "w", encoding="utf-8") as f:
            f.write(lilypond_code)
        print(f"\n✓ Guardado automáticamente: {auto_filepath}")
    except Exception as e:
        print(f"\n⚠️  No se pudo guardar automáticamente: {e}")

    # Opción de guardar en ubicación personalizada
    save_option = (
        input("\n¿Guardar también en ubicación personalizada? (s/n) [n]: ")
        .strip()
        .lower()
        or "n"
    )
    if save_option == "s":
        safe_title = re.sub(r"[^\w\s-]", "", output_config.title).strip().replace(" ", "_")
        default_filename = f"{safe_title}.ly" if safe_title else "melodia.ly"
        filename = (
            input(f"Nombre del archivo [{default_filename}]: ").strip()
            or default_filename
        )

        if not filename.endswith(".ly"):
            filename += ".ly"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(lilypond_code)
            print(f"✓ Archivo guardado: {filename}")
            print(f"  Puede abrirlo con: lilypond {filename}")
            print(f"  O en Frescobaldi para edición visual")
        except Exception as e:
            print(f"✗ Error al guardar archivo: {e}")
    else:
        print("\nPuede compilar el archivo guardado con:")
        print(f"  lilypond {auto_filepath}")
        print(f"  O abrirlo en Frescobaldi para edición visual")


def main():
    """Función principal interactiva."""
    print_header()
    print("=== CONFIGURACIÓN DE LA MELODÍA ===")
    print()

    try:
        # Obtener configuraciones
        tonal_config = get_tonal_config()
        meter_config = get_meter_config()
        rhythm_config = get_rhythm_config()
        melody_config = get_melody_config()
        motif_config = get_motif_config()
        markov_config = get_markov_config()
        expression_config = get_expression_config()
        generation_method = get_generation_method()

        # Obtener configuración genética si el método es genético
        genetic_params = None
        if generation_method == "genetic":
            genetic_params = get_genetic_config()

        # Preguntar si añadir bajo (independiente del método)
        bass_params = None
        bass_result = get_bass_config()
        if bass_result is not None:
            bass_style, bass_config = bass_result
            bass_params = {
                "bass_style": bass_style,
                "bass_config": bass_config,
            }

        tolerance = get_validation_tolerance()
        output_config = get_output_config()

        # Crear configuración completa
        config = GenerationConfig(
            tonal=tonal_config,
            meter=meter_config,
            rhythm=rhythm_config,
            melody=melody_config,
            motif=motif_config,
            markov=markov_config,
        )

        # Ejecutar generación
        staff, validation_report, bass_lilypond = run_generation_loop(
            config=config,
            tolerance=tolerance,
            generation_method=generation_method,
            expression_config=expression_config,
            genetic_params=genetic_params,
            bass_params=bass_params,
        )

        if staff is None:
            return

        # Generar código LilyPond
        architect = MelodicArchitect(config=config, expression_config=expression_config)

        # Si ya tenemos código LilyPond de generación con bajo, añadir header
        if bass_lilypond is not None:
            # Insertar título y compositor en el código existente
            header_code = ""
            if output_config.title or output_config.composer:
                header_code = "\\header {\n"
                if output_config.title:
                    header_code += f'  title = "{output_config.title}"\n'
                if output_config.composer:
                    header_code += f'  composer = "{output_config.composer}"\n'
                header_code += "}\n\n"
            lilypond_code = header_code + bass_lilypond
        else:
            lilypond_code = architect.format_as_lilypond(
                staff,
                title=output_config.title,
                composer=output_config.composer,
            )

        # Mostrar resultado
        print("\n" + "=" * 70)
        print("CÓDIGO LILYPOND")
        print("=" * 70)
        print()
        print(lilypond_code)
        print()
        print("=" * 70)
        print("¡Melodía generada exitosamente!")
        print("=" * 70)

        # Guardar
        save_output(lilypond_code, output_config, tonal_config)

        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error al generar la melodía: {e}")
        print("Por favor, verifique los parámetros ingresados.")


if __name__ == "__main__":
    main()
