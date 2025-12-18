#!/usr/bin/env python3
"""
Script de prueba para el sistema de corrección iterativa.
Simula la interacción del usuario.
"""

from melody_generator import MelodicArchitect
from melody_generator.validation import MusicValidator, AutoCorrector


def test_correction_loop():
    print("=" * 70)
    print("PRUEBA DEL SISTEMA DE CORRECCIÓN ITERATIVA")
    print("=" * 70)
    print()

    # Parámetros iniciales
    architect_params = {
        "key_name": "C",
        "mode": "major",
        "meter_tuple": (4, 4),
        "num_measures": 4,
        "rhythmic_complexity": 2,
        "infraction_rate": 0.1,
        "max_interval": 6,
        "use_markov": False,
    }

    architect = MelodicArchitect(**architect_params)

    # Intentar hasta 3 veces
    for attempt in range(1, 4):
        print(f"\n{'─' * 70}")
        print(f"Intento {attempt}")
        print(f"{'─' * 70}\n")

        # Generar melodía
        print("Generando melodía...")
        staff = architect.generate_period()

        # Validar
        print("Validando...\n")
        validator = MusicValidator(
            staff=staff,
            lilypond_formatter=architect.lilypond_formatter,
            expected_key="C",
            expected_mode="major",
            expected_meter=(4, 4),
            tolerance=0.65,
        )

        report = validator.validate_all()

        # Mostrar resultados
        print(f"Puntuación: {report.overall_score:.1%}")
        print(f"Válida: {report.is_valid}")
        print(f"Key matches: {report.key_validation.matches}")
        print(f"Meter valid: {report.meter_validation.is_valid}")

        if report.is_valid:
            print(f"\n✓ Validación exitosa en intento {attempt}")
            break
        else:
            # Mostrar correcciones
            corrector = AutoCorrector(report)
            print(f"\n{corrector.get_correction_summary()}")

            # Aplicar correcciones
            print("\nAplicando correcciones...")
            architect_params = corrector.apply_to_architect_params(architect_params)

            # Mostrar cambios
            print(f"  → Complejidad rítmica: {architect_params['rhythmic_complexity']}")
            print(f"  → Max interval: {architect_params['max_interval']}")
            print(f"  → Infraction rate: {architect_params['infraction_rate']:.3f}")

            # Recrear architect
            architect = MelodicArchitect(**architect_params)

    print("\n" + "=" * 70)
    print("Prueba completada")
    print("=" * 70)


if __name__ == "__main__":
    test_correction_loop()
