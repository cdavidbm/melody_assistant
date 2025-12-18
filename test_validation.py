#!/usr/bin/env python3
"""
Test script for the validation system.
Generates a simple melody and validates it.
"""

from melody_generator import MelodicArchitect
from melody_generator.validation import MusicValidator


def test_validation():
    print("=" * 70)
    print("PRUEBA DEL SISTEMA DE VALIDACIÓN")
    print("=" * 70)
    print()

    # Create a simple melody
    print("Generando melodía de prueba (C major, 4/4, 4 compases)...\n")

    architect = MelodicArchitect(
        key_name="C",
        mode="major",
        meter_tuple=(4, 4),
        num_measures=4,
        rhythmic_complexity=1,
        use_markov=False,
    )

    staff = architect.generate_period()

    # Validate it
    print("Validando melodía...\n")

    validator = MusicValidator(
        staff=staff,
        lilypond_formatter=architect.lilypond_formatter,
        expected_key="C",
        expected_mode="major",
        expected_meter=(4, 4),
        tolerance=0.65,
    )

    report = validator.validate_all()

    # Print detailed report
    print(report.format_detailed_report())

    # Test auto-corrector
    if not report.is_valid:
        print("\n" + "=" * 70)
        print("SUGERENCIAS DEL AUTO-CORRECTOR")
        print("=" * 70)
        print()

        from melody_generator.validation import AutoCorrector

        corrector = AutoCorrector(report)
        print(corrector.get_correction_summary())
        print()
        print("Correcciones detalladas:")
        corrections = corrector.suggest_corrections()
        for key, value in corrections.items():
            print(f"  • {key}: {value}")

    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    if report.is_valid:
        print("✓ La melodía pasó la validación")
    else:
        print(
            f"⚠️  La melodía requiere ajustes (puntuación: {report.overall_score:.1%})"
        )

    return report.is_valid


if __name__ == "__main__":
    test_validation()
