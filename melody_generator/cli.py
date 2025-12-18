"""
Interfaz de línea de comandos para el generador de melodías.
"""

import re

from .models import ImpulseType
from .architect import MelodicArchitect


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


def parse_subdivisions(numerator: int) -> list:
    """Parsea las subdivisiones para métricas amalgama."""
    if numerator == 5:
        subdiv_input = input("  Ej: 2+3 o 3+2 [2+3]: ").strip() or "2+3"
    elif numerator == 7:
        subdiv_input = input("  Ej: 2+2+3 o 3+2+2 [2+2+3]: ").strip() or "2+2+3"
    else:
        subdiv_input = input(f"  Separados por + (deben sumar {numerator}): ").strip()

    return [int(x) for x in subdiv_input.split("+")]


def main():
    """Función principal interactiva."""

    print("=" * 70)
    print("GENERADOR DE MELODÍAS - PROTOCOLO SYMMETRY & LOGIC")
    print("=" * 70)
    print()
    print("Este programa genera melodías basadas en teoría musical clásica.")
    print()

    print("=== CONFIGURACIÓN DE LA MELODÍA ===")
    print()

    # Tonalidad
    key_name = input("Tonalidad (ej: C, D, Eb, F#) [C]: ").strip() or "C"

    # Modo
    print_mode_menu()
    mode_choice = input("\nSeleccione modo [1]: ").strip() or "1"
    mode = MODE_MAP.get(mode_choice, "major")

    # Compás
    print("\nCompás:")
    numerator = int(input("  Numerador (pulsos por compás) [4]: ").strip() or "4")
    denominator = int(input("  Denominador (figura que cuenta) [4]: ").strip() or "4")
    meter_tuple = (numerator, denominator)

    # Subdivisiones para métricas amalgama
    subdivisions = None
    if numerator in [5, 7, 11]:
        print(f"\nMétrica amalgama detectada ({numerator}/{denominator})")
        print(f"¿Cómo subdividir los {numerator} pulsos?")
        subdivisions = parse_subdivisions(numerator)

    # Número de compases
    num_measures = int(input("\nNúmero de compases [8]: ").strip() or "8")

    # Tipo de impulso
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

    # Complejidad rítmica
    print("\nComplejidad rítmica:")
    print("1. Simple (negras y corcheas)")
    print("2. Moderado (incluye puntillos)")
    print("3. Complejo (semicorcheas y subdivisiones)")
    complexity = int(input("Seleccione [2]: ").strip() or "2")

    # Usar silencios
    use_rests_input = (
        input("\n¿Usar silencios como respiraciones? (s/n) [s]: ").strip().lower()
        or "s"
    )
    use_rests = use_rests_input == "s"

    # Usar tenoris
    use_tenoris_input = (
        input("¿Usar 'tenoris' (quinta como nota sostenedora)? (s/n) [n]: ")
        .strip()
        .lower()
        or "n"
    )
    use_tenoris = use_tenoris_input == "s"

    # Posición del clímax
    climax_input = input("\nPosición del clímax (0.0-1.0) [0.75]: ").strip()
    climax_pos = float(climax_input) if climax_input else 0.75

    # Libertad de variación
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

    # Cadenas de Markov
    print("\n=== CADENAS DE MARKOV (Aprendizaje de Compositores Clásicos) ===")
    print()
    print("Las cadenas de Markov permiten que el generador aprenda patrones")
    print("melódicos y rítmicos de compositores clásicos del corpus de music21.")
    print()

    use_markov_input = (
        input("¿Usar cadenas de Markov? (s/n) [n]: ").strip().lower() or "n"
    )
    use_markov = use_markov_input == "s"

    markov_composer = "bach"
    markov_weight = 0.5
    markov_order = 2

    if use_markov:
        print("\nCompositor de referencia:")
        print("1. Bach (363 obras - estilo contrapuntístico)")
        print("2. Mozart (11 obras - estilo clásico elegante)")
        print("3. Beethoven (23 obras - estilo dramático)")
        print("4. Combinado (mezcla de los tres estilos)")

        composer_choice = input("Seleccione compositor [1]: ").strip() or "1"
        composer_map = {"1": "bach", "2": "mozart", "3": "beethoven", "4": "combined"}
        markov_composer = composer_map.get(composer_choice, "bach")

        print("\nPeso de Markov (influencia en la generación):")
        print("  0.0 = No influye (solo reglas teóricas)")
        print("  0.5 = Balance equilibrado (recomendado)")
        print("  1.0 = Máxima influencia de Markov")

        weight_input = input("Peso de Markov (0.0-1.0) [0.5]: ").strip()
        if weight_input:
            try:
                markov_weight = float(weight_input)
                markov_weight = max(0.0, min(1.0, markov_weight))
            except ValueError:
                markov_weight = 0.5

        print("\nOrden de la cadena (contexto previo):")
        print("  1 = Solo intervalo/ritmo previo (menos contexto)")
        print("  2 = Dos pasos previos (recomendado)")
        print("  3 = Tres pasos previos (máximo contexto)")

        order_input = input("Orden [2]: ").strip()
        if order_input in ["1", "2", "3"]:
            markov_order = int(order_input)

    # Tipo de generación
    print("\nMétodo de generación:")
    print("1. Tradicional (sistema actual, cohesión rítmica)")
    print("2. Jerárquico (NUEVO: Motivo → Frase → Semifrase → Período)")
    generation_method_input = input("Seleccione método [1]: ").strip() or "1"
    use_hierarchical = generation_method_input == "2"

    # Título y compositor
    print("\n=== INFORMACIÓN DE LA PARTITURA ===")
    title = input("Título [Melodía Generada]: ").strip() or "Melodía Generada"
    composer = (
        input("Compositor [MelodicArchitect AI]: ").strip() or "MelodicArchitect AI"
    )

    print("\n" + "=" * 70)
    print("Generando melodía...")
    print("=" * 70)
    print()

    try:
        architect = MelodicArchitect(
            key_name=key_name,
            mode=mode,
            meter_tuple=meter_tuple,
            subdivisions=subdivisions,
            num_measures=num_measures,
            impulse_type=impulse_type,
            infraction_rate=0.1,
            rhythmic_complexity=complexity,
            use_rests=use_rests,
            rest_probability=0.15,
            use_motivic_variations=True,
            variation_probability=0.4,
            climax_position=climax_pos,
            climax_intensity=1.5,
            max_interval=6,
            use_tenoris=use_tenoris,
            tenoris_probability=0.2,
            variation_freedom=variation_freedom,
            use_markov=use_markov,
            markov_composer=markov_composer,
            markov_weight=markov_weight,
            markov_order=markov_order,
        )

        if use_hierarchical:
            print("Usando método JERÁRQUICO (Motivo → Frase → Semifrase → Período)")
            staff = architect.generate_period_hierarchical()
            lilypond_code = architect.format_as_lilypond(
                staff, title=title, composer=composer
            )
        else:
            print("Usando método TRADICIONAL (cohesión rítmica)")
            lilypond_code = architect.generate_and_display(
                title=title, composer=composer
            )

        print(lilypond_code)
        print()
        print("=" * 70)
        print("¡Melodía generada exitosamente!")
        print("=" * 70)

        # Opción de guardar en archivo
        save_option = (
            input("\n¿Guardar en archivo .ly? (s/n) [n]: ").strip().lower() or "n"
        )
        if save_option == "s":
            safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")
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
            print("Copie el código LilyPond anterior y péguelo en Frescobaldi")
            print("o guárdelo manualmente en un archivo .ly para compilarlo.")

        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error al generar la melodía: {e}")
        print("Por favor, verifique los parámetros ingresados.")


if __name__ == "__main__":
    main()
