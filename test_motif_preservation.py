#!/usr/bin/env python3
"""
Test script to verify that develop_user_motif_v2 preserves the original motif.

This tests the fix for the critical bug where the user's motif was being ignored.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from melody_generator import MelodicArchitect, GenerationConfig
from melody_generator.config import TonalConfig, MeterConfig
from melody_generator.lilypond_validator import validate_motif_for_development

# User's test motif with full articulations, dynamics, ligaduras
TEST_MOTIF = """
{
    \\time 4/4
    \\key c \\minor
    \\clef "treble"
    \\set strictBeatBeaming = ##t
    g'4-- \\mf( c''4 d''8 \\< es''8-.)
    d''4-> \\f \\!( |
    b'4 \\> c''4 \\p b'8 \\!) c''8 \\mf(
    g'4 |
    g'4 \\< f'4) g'8 \\f \\!( d'8 \\>
    d'4 \\p |
    es'4 \\p \\!) f'4--( es'8 g'8
    c'4) \\bar "|."
  }
"""


def test_motif_preservation():
    """Test that the original motif is preserved in the output."""

    print("=" * 70)
    print("TEST: Verificar preservación del motivo original")
    print("=" * 70)

    # Step 1: Validate the motif
    print("\n[1] Validando motivo con LilyPond + music21...")
    validation = validate_motif_for_development(
        fragment=TEST_MOTIF,
        key_name="C",
        mode="minor",
        meter_num=4,
        meter_den=4,
    )

    if not validation.is_valid:
        print(f"ERROR: Validación falló: {validation.error_message}")
        return False

    print(f"    ✓ Notas: {validation.note_count}")
    print(f"    ✓ Duración: {validation.duration_beats} beats")
    print(f"    ✓ Compases: {validation.duration_beats / 4}")
    print(f"    ✓ Tonalidad detectada: {validation.detected_key} {validation.detected_mode}")
    print(f"    ✓ music21_stream: {type(validation.music21_stream)}")

    # Step 2: Create architect with matching config
    print("\n[2] Creando MelodicArchitect...")
    config = GenerationConfig(
        tonal=TonalConfig(key_name="C", mode="minor"),
        meter=MeterConfig(meter_tuple=(4, 4), num_measures=8),
    )
    architect = MelodicArchitect(config=config)
    print("    ✓ Arquitecto creado")

    # Step 3: Call develop_user_motif_v2
    print("\n[3] Llamando develop_user_motif_v2...")
    staff, lilypond_code = architect.develop_user_motif_v2(
        original_lilypond=TEST_MOTIF,
        music21_stream=validation.music21_stream,
        num_measures=8,
        variation_freedom=2,
        add_bass=False,
        title="Test Preservación Motivo",
        composer="Test",
    )
    print("    ✓ Generación completada")

    # Step 4: Verify the original motif elements are in the output
    print("\n[4] Verificando preservación de elementos originales...")

    # Key elements that MUST be preserved (articulations, dynamics, etc.)
    must_preserve = [
        "g'4--",      # First note with tenuto
        "\\mf",       # mezzo-forte dynamic
        "c''4",       # Second note
        "d''8",       # Eighth note
        "es''8-.",    # Staccato
        "\\<",        # Crescendo
        "d''4->",     # Accent
        "\\f",        # forte
        "\\!",        # Crescendo end
        "b'4",        # B natural
        "\\>",        # Decrescendo
        "\\p",        # piano
        "c''8",       # Eighth note C
    ]

    found = 0
    missing = []

    for element in must_preserve:
        if element in lilypond_code:
            found += 1
            print(f"    ✓ Encontrado: {element}")
        else:
            missing.append(element)
            print(f"    ✗ FALTA: {element}")

    # Step 5: Check for "MOTIVO ORIGINAL" comment
    print("\n[5] Verificando marcador de sección...")
    if "MOTIVO ORIGINAL" in lilypond_code:
        print("    ✓ Sección 'MOTIVO ORIGINAL' encontrada")
    else:
        print("    ✗ Falta marcador 'MOTIVO ORIGINAL'")
        missing.append("MOTIVO ORIGINAL marker")

    # Step 6: Check for development section
    print("\n[6] Verificando sección de desarrollo...")
    if "DESARROLLO" in lilypond_code:
        print("    ✓ Sección 'DESARROLLO' encontrada")
    else:
        print("    ⚠ Falta marcador 'DESARROLLO' (puede ser opcional)")

    # Step 7: Save output for inspection
    output_path = Path(__file__).parent / "output" / "test_motif_preservation.ly"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        f.write(lilypond_code)
    print(f"\n[7] Output guardado: {output_path}")

    # Summary
    print("\n" + "=" * 70)
    print("RESUMEN:")
    print("=" * 70)
    print(f"  Elementos verificados: {len(must_preserve)}")
    print(f"  Encontrados: {found}")
    print(f"  Faltantes: {len(missing)}")

    if missing:
        print(f"\n  ELEMENTOS FALTANTES: {missing}")

    success = len(missing) == 0

    if success:
        print("\n  ✓✓✓ TEST PASSED: Motivo preservado correctamente ✓✓✓")
    else:
        print("\n  ✗✗✗ TEST FAILED: Algunos elementos no se preservaron ✗✗✗")

    # Print full LilyPond for inspection
    print("\n" + "=" * 70)
    print("LILYPOND GENERADO:")
    print("=" * 70)
    print(lilypond_code[:2000])  # First 2000 chars
    if len(lilypond_code) > 2000:
        print(f"\n... (truncado, total: {len(lilypond_code)} caracteres)")

    return success


if __name__ == "__main__":
    success = test_motif_preservation()
    sys.exit(0 if success else 1)
