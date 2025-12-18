#!/usr/bin/env python3
"""
Script para entrenar modelos de Markov desde el corpus de music21.

Uso:
    python scripts/train_markov.py --composer bach --type melody --order 2
    python scripts/train_markov.py --composer all --type both --order 2
    python scripts/train_markov.py --help
"""

import argparse
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from melody_generator.markov import MelodicMarkovModel, RhythmicMarkovModel


def train_melody_model(composer: str, order: int, max_works: int | None = None):
    """
    Entrena modelo melódico.

    Args:
        composer: "bach", "mozart", "beethoven", "all"
        order: Orden de la cadena de Markov (1-3)
        max_works: Máximo de obras a procesar (None = todas)
    """
    print(f"\n{'=' * 70}")
    print(f"ENTRENANDO MODELO MELÓDICO: {composer.upper()}")
    print(f"{'=' * 70}")
    print(f"Orden: {order}")
    print(f"Máximo de obras: {max_works or 'todas'}")
    print()

    model = MelodicMarkovModel(order=order, composer=composer)

    try:
        model.train_from_corpus(
            composer=composer,
            max_works=max_works,
            voice_part=0,  # Voz superior
        )
    except Exception as e:
        print(f"\n❌ Error durante el entrenamiento: {e}")
        return False

    print(f"\nTotal de transiciones aprendidas: {model.chain.total_transitions}")

    # Guardar modelo
    output_dir = Path("models/melody_markov")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{composer}_intervals.json"

    try:
        model.chain.save(str(output_path))
        print(f"\n✓ Modelo guardado en: {output_path}")

        # Mostrar tamaño del archivo
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Tamaño del archivo: {size_mb:.2f} MB")
        print()
        return True

    except Exception as e:
        print(f"\n❌ Error al guardar modelo: {e}")
        return False


def train_rhythm_model(composer: str, order: int, max_works: int | None = None):
    """
    Entrena modelo rítmico.

    Args:
        composer: "bach", "mozart", "beethoven", "all"
        order: Orden de la cadena de Markov (1-3)
        max_works: Máximo de obras a procesar (None = todas)
    """
    print(f"\n{'=' * 70}")
    print(f"ENTRENANDO MODELO RÍTMICO: {composer.upper()}")
    print(f"{'=' * 70}")
    print(f"Orden: {order}")
    print(f"Máximo de obras: {max_works or 'todas'}")
    print()

    model = RhythmicMarkovModel(order=order, composer=composer)

    try:
        model.train_from_corpus(composer=composer, max_works=max_works, voice_part=0)
    except Exception as e:
        print(f"\n❌ Error durante el entrenamiento: {e}")
        return False

    print(f"\nTotal de transiciones aprendidas: {model.chain.total_transitions}")

    # Guardar modelo
    output_dir = Path("models/rhythm_markov")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{composer}_rhythms.json"

    try:
        model.chain.save(str(output_path))
        print(f"\n✓ Modelo guardado en: {output_path}")

        # Mostrar tamaño del archivo
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  Tamaño del archivo: {size_mb:.2f} MB")
        print()
        return True

    except Exception as e:
        print(f"\n❌ Error al guardar modelo: {e}")
        return False


def combine_models(model_type: str, order: int):
    """
    Combina modelos de Bach, Mozart y Beethoven en uno solo.

    Args:
        model_type: "melody" o "rhythm"
        order: Orden de la cadena
    """
    print(f"\n{'=' * 70}")
    print(f"COMBINANDO MODELOS {model_type.upper()}")
    print(f"{'=' * 70}")
    print()

    if model_type == "melody":
        from melody_generator.markov import MelodicMarkovModel, MarkovChain

        combined = MelodicMarkovModel(order=order, composer="combined")
        model_dir = Path("models/melody_markov")
        composers = ["bach", "mozart", "beethoven"]
        suffix = "intervals"
    else:
        from melody_generator.markov import RhythmicMarkovModel, MarkovChain

        combined = RhythmicMarkovModel(order=order, composer="combined")
        model_dir = Path("models/rhythm_markov")
        composers = ["bach", "mozart", "beethoven"]
        suffix = "rhythms"

    # Cargar y combinar modelos individuales
    for composer in composers:
        model_path = model_dir / f"{composer}_{suffix}.json"

        if not model_path.exists():
            print(f"⚠️  Modelo {composer} no encontrado, omitiendo...")
            continue

        print(f"  Cargando modelo de {composer}...")
        temp_chain = MarkovChain(order=order)
        temp_chain.load(str(model_path))

        # Combinar transiciones
        for state_key, next_states in temp_chain.transitions.items():
            if state_key not in combined.chain.transitions:
                combined.chain.transitions[state_key] = {}

            for next_state, count in next_states.items():
                if next_state not in combined.chain.transitions[state_key]:
                    combined.chain.transitions[state_key][next_state] = 0
                combined.chain.transitions[state_key][next_state] += count
                combined.chain.total_transitions += count

    # Guardar modelo combinado
    output_path = model_dir / f"combined_{suffix}.json"
    combined.chain.save(str(output_path))

    print(f"\n✓ Modelo combinado guardado en: {output_path}")
    print(f"  Total de transiciones: {combined.chain.total_transitions}")

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Tamaño del archivo: {size_mb:.2f} MB")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Entrena modelos de Markov desde corpus de music21",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  
  # Entrenar solo modelo melódico de Bach
  python scripts/train_markov.py --composer bach --type melody
  
  # Entrenar modelos melódico y rítmico de Mozart
  python scripts/train_markov.py --composer mozart --type both
  
  # Entrenar todos los compositores (Bach, Mozart, Beethoven)
  python scripts/train_markov.py --composer all --type both
  
  # Entrenar con límite de obras (útil para pruebas rápidas)
  python scripts/train_markov.py --composer bach --type melody --max-works 50
  
  # Entrenar con orden 3 (más contexto)
  python scripts/train_markov.py --composer beethoven --type both --order 3
        """,
    )

    parser.add_argument(
        "--composer",
        choices=["bach", "mozart", "beethoven", "all"],
        default="bach",
        help="Compositor para entrenar (default: bach)",
    )
    parser.add_argument(
        "--type",
        choices=["melody", "rhythm", "both"],
        default="both",
        help="Tipo de modelo a entrenar (default: both)",
    )
    parser.add_argument(
        "--order",
        type=int,
        choices=[1, 2, 3],
        default=2,
        help="Orden de la cadena de Markov (default: 2)",
    )
    parser.add_argument(
        "--max-works",
        type=int,
        default=None,
        help="Máximo de obras a procesar por compositor (default: todas)",
    )
    parser.add_argument(
        "--no-combine",
        action="store_true",
        help="No crear modelo combinado cuando se usa --composer all",
    )

    args = parser.parse_args()

    print(f"\n{'=' * 70}")
    print(f"ENTRENADOR DE MODELOS MARKOV - MELODY ASSISTANT")
    print(f"{'=' * 70}")
    print(f"\nConfiguración:")
    print(f"  Compositor(es): {args.composer}")
    print(f"  Tipo(s): {args.type}")
    print(f"  Orden: {args.order}")
    print(f"  Máximo de obras: {args.max_works or 'Todas disponibles'}")
    print()

    # Determinar compositores a entrenar
    if args.composer == "all":
        composers = ["bach", "mozart", "beethoven"]
    else:
        composers = [args.composer]

    # Entrenar modelos
    success_melody = []
    success_rhythm = []

    for composer in composers:
        if args.type in ["melody", "both"]:
            if train_melody_model(composer, args.order, args.max_works):
                success_melody.append(composer)

        if args.type in ["rhythm", "both"]:
            if train_rhythm_model(composer, args.order, args.max_works):
                success_rhythm.append(composer)

    # Crear modelos combinados si entrenamos todos
    if args.composer == "all" and not args.no_combine:
        if args.type in ["melody", "both"] and len(success_melody) >= 2:
            combine_models("melody", args.order)

        if args.type in ["rhythm", "both"] and len(success_rhythm) >= 2:
            combine_models("rhythm", args.order)

    # Resumen final
    print(f"\n{'=' * 70}")
    print("RESUMEN FINAL")
    print(f"{'=' * 70}")

    if args.type in ["melody", "both"]:
        print(f"\nModelos melódicos entrenados exitosamente: {len(success_melody)}")
        for comp in success_melody:
            print(f"  ✓ {comp}")

    if args.type in ["rhythm", "both"]:
        print(f"\nModelos rítmicos entrenados exitosamente: {len(success_rhythm)}")
        for comp in success_rhythm:
            print(f"  ✓ {comp}")

    print(f"\n{'=' * 70}")
    print("¡Entrenamiento completado!")
    print(f"{'=' * 70}")
    print("\nLos modelos están listos para usar con el generador de melodías.")
    print("Ejecuta: python main.py")
    print()


if __name__ == "__main__":
    main()
